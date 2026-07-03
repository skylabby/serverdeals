"""
eBay Buy Browse API client for the ServerDeals scraper.

Uses the modern REST Buy Browse API (JSON) with OAuth 2.0 client-credentials
grant instead of the deprecated XML Finding API. Handles auth, token refresh,
pagination, rate limiting, and retry/backoff.
"""

from __future__ import annotations

import logging
import time
from base64 import b64encode
from dataclasses import dataclass, field
from typing import Optional

import httpx

from . import config

logger = logging.getLogger(__name__)


# ── Dataclasses (same shape as before — compatible with store/scheduler) ──


@dataclass
class EBayListing:
    """Parsed eBay listing from the Buy Browse API response."""

    item_id: str
    title: str
    current_price: float
    currency_id: str
    condition: str
    condition_id: int
    listing_type: str
    end_time: str       # ISO 8601 — mapped from itemCreationDate
    gallery_url: str    # mapped from image.imageUrl
    view_item_url: str  # mapped from itemWebUrl
    category_id: str = ""
    category_name: str = ""
    location: str = ""
    shipping_type: str = ""
    shipping_cost: float = 0.0
    bids: int = 0
    is_top_rated: bool = False
    raw: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Result of an eBay search operation."""

    items: list[EBayListing]
    total_entries: int
    page_number: int
    entries_per_page: int
    query_keywords: str
    category_id: Optional[int] = None


# ── Helpers ──────────────────────────────────────────────────────────────


def _map_buying_options(options: list[str]) -> str:
    """Map buyingOptions array to a listing type string."""
    if not options:
        return "FixedPrice"
    if "AUCTION" in options:
        return "Auction"
    if "FIXED_PRICE" in options:
        return "FixedPrice"
    return options[0]


def _parse_buy_listing(item: dict) -> EBayListing:
    """Parse a single item_summary entry into an EBayListing."""

    price = item.get("price", {})
    image = item.get("image", {})
    shipping = (item.get("shippingOptions") or [{}])[0].get("shippingCost", {})
    location = item.get("itemLocation", {})
    leaf_cats = item.get("leafCategoryIds") or []

    return EBayListing(
        item_id=item.get("itemId", ""),
        title=item.get("title", ""),
        current_price=float(price.get("value", 0) or 0),
        currency_id=price.get("currency", "USD"),
        condition=item.get("condition", "N/A"),
        condition_id=int(item.get("conditionId", "3000") or 3000),
        listing_type=_map_buying_options(item.get("buyingOptions") or []),
        end_time=item.get("itemCreationDate", ""),
        gallery_url=image.get("imageUrl", ""),
        view_item_url=item.get("itemWebUrl", ""),
        category_id=leaf_cats[0] if leaf_cats else "",
        category_name="",
        location=location.get("country", "US"),
        shipping_type="",
        shipping_cost=float(shipping.get("value", 0) or 0),
        bids=0,
        is_top_rated=False,
        raw=item,
    )


# ─────────────────────────────────────────────────────────────────────────
#  eBay OAuth 2.0 token manager
# ─────────────────────────────────────────────────────────────────────────


class _TokenManager:
    """Lazy OAuth token fetcher with caching and auto-refresh."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0

    @property
    def token(self) -> str:
        """Return a valid OAuth token, refreshing if expired."""
        if self._token is None or time.monotonic() > self._expires_at - 120:
            self._refresh()
        assert self._token is not None
        return self._token

    def _refresh(self) -> None:
        """Fetch a new Application Access Token via client_credentials grant."""
        credentials = f"{config.EBAY_APP_ID}:{config.EBAY_CERT_ID}"
        encoded = b64encode(credentials.encode()).decode()

        with httpx.Client(timeout=config.REQUEST_TIMEOUT) as client:
            resp = client.post(
                config.EBAY_OAUTH_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": config.EBAY_OAUTH_SCOPE,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        self._token = data["access_token"]
        self._expires_at = time.monotonic() + data.get("expires_in", 7200)
        logger.debug("OAuth token refreshed (expires in %ds)", data.get("expires_in", 7200))


# ─────────────────────────────────────────────────────────────────────────
#  eBay Client
# ─────────────────────────────────────────────────────────────────────────


class EBayClient:
    """Synchronous eBay Buy Browse API client with rate limiting and retries."""

    def __init__(
        self,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._token_mgr = _TokenManager()
        self._last_call_time: float = 0.0
        self._http = http_client

        # Validate credentials
        if not config.EBAY_APP_ID:
            raise ValueError(
                "EBAY_APP_ID is required. Set it in .env."
            )
        if not config.EBAY_CERT_ID:
            raise ValueError(
                "EBAY_CERT_ID is required. Set it in .env."
            )

    # ── HTTP plumbing ────────────────────────────────────────────────

    @property
    def _client(self) -> httpx.Client:
        """Lazy-created httpx Client (shared connection pool)."""
        if self._http is None:
            self._http = httpx.Client(
                timeout=config.REQUEST_TIMEOUT,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "ServerDeals/1.0 (python-httpx)",
                },
            )
        return self._http

    def _rate_limit(self) -> None:
        """Enforce minimum interval between API calls."""
        elapsed = time.monotonic() - self._last_call_time
        if elapsed < config.MIN_CALL_INTERVAL_SEC:
            time.sleep(config.MIN_CALL_INTERVAL_SEC - elapsed)

    def _call_api(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict:
        """
        Make a single API call with retry+backoff and OAuth auth.

        Returns parsed JSON dict.
        """
        params = params or {}
        url = f"{config.EBAY_BUY_BROWSE_BASE}/{path.lstrip('/')}"

        last_exception: Exception | None = None
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                self._rate_limit()
                self._last_call_time = time.monotonic()

                logger.debug("eBay API call: %s?%s", url[:100], str(params)[:100])

                resp = self._client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self._token_mgr.token}",
                        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                    },
                )

                if resp.status_code == 200:
                    return resp.json()

                if resp.status_code == 401:
                    # Token expired — force refresh and retry once
                    logger.info("OAuth token expired — refreshing")
                    self._token_mgr._refresh()
                    continue

                if resp.status_code in config.RETRYABLE_STATUS_CODES:
                    logger.warning(
                        "eBay API returned %d (attempt %d/%d)",
                        resp.status_code,
                        attempt + 1,
                        config.MAX_RETRIES + 1,
                    )
                else:
                    resp.raise_for_status()

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.warning(
                    "eBay API network error (attempt %d/%d): %s",
                    attempt + 1,
                    config.MAX_RETRIES + 1,
                    exc,
                )
                last_exception = exc

            # Exponential backoff before retry
            if attempt < config.MAX_RETRIES:
                delay = config.RETRY_BACKOFF_BASE * (2**attempt)
                logger.info("Retrying in %.1fs …", delay)
                time.sleep(delay)

        raise last_exception or RuntimeError("eBay API call failed after all retries")

    # ── Public API ───────────────────────────────────────────────────

    def search_items(
        self,
        keywords: str,
        category_id: int | None = None,
        limit: int | None = None,
        max_pages: int | None = None,
    ) -> SearchResult:
        """
        Search active eBay listings via Buy Browse API.

        Args:
            keywords: Search keywords.
            category_id: Optional eBay category ID to filter by.
            limit: Max total items to return (aggregates across pages).
            max_pages: Max pages to fetch (defaults to config.MAX_PAGES_PER_CATEGORY).

        Returns:
            SearchResult with combined items from all fetched pages.
        """
        pages_limit = max_pages if max_pages is not None else config.MAX_PAGES_PER_CATEGORY
        items_limit = limit or pages_limit * config.PAGE_SIZE
        entries_per_page = min(config.PAGE_SIZE, 200)  # Buy API max is 200

        all_items: list[EBayListing] = []
        offset = 0
        api_total = 0

        for page in range(1, pages_limit + 1):
            params: dict[str, str] = {
                "q": keywords,
                "limit": str(entries_per_page),
                "offset": str(offset),
            }
            if category_id is not None:
                params["category_ids"] = str(category_id)

            try:
                data = self._call_api("item_summary/search", params)
            except Exception as exc:
                raise EBayAPIError(str(exc))

            item_summaries = data.get("itemSummaries") or []
            for item_data in item_summaries:
                try:
                    all_items.append(_parse_buy_listing(item_data))
                except Exception:
                    logger.exception("Failed to parse a listing; skipping")

            total = data.get("total", 0)
            api_total = total
            logger.info(
                "Category %s: page %d → %d items (total so far: %d, API total: %d)",
                category_id or "all",
                page,
                len(item_summaries),
                len(all_items),
                total,
            )

            # Stop conditions
            if len(all_items) >= items_limit:
                break
            if len(item_summaries) < entries_per_page:
                # Last page — exhausted
                break
            if offset + len(item_summaries) >= total:
                break

            offset += entries_per_page

        # Trim to exact limit if needed
        if items_limit and len(all_items) > items_limit:
            all_items = all_items[:items_limit]

        return SearchResult(
            items=all_items,
            total_entries=api_total,
            page_number=1,
            entries_per_page=entries_per_page,
            query_keywords=keywords,
            category_id=category_id,
        )

    def get_completed_items(
        self,
        keywords: str,
        category_id: int | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        """
        Search completed (sold) eBay listings for price history.

        NOTE: The Buy Browse API does not support completed-item search.
        This method is retained for API compatibility but raises NotImplementedError.
        Consider using the eBay Analytics API or Marketplace Insights API for
        price history data.
        """
        raise NotImplementedError(
            "Completed-item search is not available via the Buy Browse API. "
            "Consider using the eBay Analytics API for Terapeak price data."
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http:
            self._http.close()
            self._http = None

    def __enter__(self) -> "EBayClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


# ─────────────────────────────────────────────────────────────────────────
#  Exceptions
# ─────────────────────────────────────────────────────────────────────────


class EBayAPIError(Exception):
    """Raised when the eBay API returns an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
