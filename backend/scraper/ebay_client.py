"""
eBay Finding API client for the ServerDeals scraper.

Talks to the eBay Finding Service (XML-based) to search active listings
and completed (sold) items for price history. Handles auth, pagination,
rate limiting, retry/backoff, and XML parsing.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode

import httpx

from . import config

logger = logging.getLogger(__name__)

# ── eBay Finding API XML namespaces ─────────────────────────────────────
_NS = "http://www.ebay.com/marketplace/search/v1/services"


@dataclass
class EBayListing:
    """Parsed eBay listing from the Finding API response."""

    item_id: str
    title: str
    current_price: float
    currency_id: str
    condition: str
    condition_id: int
    listing_type: str
    end_time: str  # ISO 8601
    gallery_url: str
    view_item_url: str
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


def _ns(tag: str) -> str:
    """Qualify a tag name with the Finding API namespace."""
    return f"{{{_NS}}}{tag}"


def _text(el: ET.Element | None, default: str = "") -> str:
    """Safely get element text, returning default on None/missing."""
    return el.text.strip() if el is not None and el.text else default


def _float_text(el: ET.Element | None, default: float = 0.0) -> float:
    """Safely get element text as float."""
    if el is None or not el.text:
        return default
    try:
        return float(el.text.strip())
    except (ValueError, TypeError):
        return default


def _int_text(el: ET.Element | None, default: int = 0) -> int:
    """Safely get element text as int."""
    if el is None or not el.text:
        return default
    try:
        return int(el.text.strip())
    except (ValueError, TypeError):
        return default


def _parse_listing(item_el: ET.Element) -> EBayListing:
    """Parse a single <item> element into an EBayListing."""

    def find(path: str) -> ET.Element | None:
        """Walk a slash-separated path of namespace-qualified tags."""
        current = item_el
        for part in path.split("/"):
            child = current.find(_ns(part))
            if child is None:
                return None
            current = child
        return current

    # Primary listing info
    listing_type_el = find("listingInfo/listingType")
    listing_type = _text(listing_type_el)

    price_el = find("sellingStatus/convertedCurrentPrice")
    currency_id = price_el.attrib.get("currencyId", "USD") if price_el is not None else "USD"

    return EBayListing(
        item_id=_text(find("itemId")),
        title=_text(find("title")),
        current_price=_float_text(price_el),
        currency_id=currency_id,
        condition=_text(find("condition/conditionDisplayName")),
        condition_id=_int_text(find("condition/conditionId")),
        listing_type=listing_type,
        end_time=_text(find("listingInfo/endTime")),
        gallery_url=_text(find("galleryURL")),
        view_item_url=_text(find("viewItemURL")),
        category_id=_text(find("primaryCategory/categoryId")),
        category_name=_text(find("primaryCategory/categoryName")),
        location=_text(find("location")),
        shipping_type=_text(find("shippingInfo/shippingType")),
        shipping_cost=_float_text(find("shippingInfo/shippingServiceCost")),
        bids=_int_text(find("sellingStatus/bidCount")),
        is_top_rated=_text(find("topRatedListing")).lower() == "true",
    )


# ─────────────────────────────────────────────────────────────────────────
#  eBay Client
# ─────────────────────────────────────────────────────────────────────────


class EBayClient:
    """Synchronous eBay Finding API client with rate limiting and retries."""

    def __init__(
        self,
        app_id: str | None = None,
        endpoint: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._app_id = app_id or config.EBAY_APP_ID
        self._endpoint = endpoint or config.EBAY_FINDING_ENDPOINT
        self._last_call_time: float = 0.0
        self._http = http_client  # Allow injection for testing

        if not self._app_id:
            raise ValueError(
                "EBAY_APP_ID is required. Set it in .env or pass app_id= explicitly."
            )

    # ── HTTP plumbing ────────────────────────────────────────────────

    @property
    def _client(self) -> httpx.Client:
        """Lazy-created httpx Client (shared connection pool)."""
        if self._http is None:
            self._http = httpx.Client(
                timeout=config.REQUEST_TIMEOUT,
                headers={
                    "Accept": "application/xml",
                    "User-Agent": "ServerDeals/1.0 (python-httpx)",
                },
            )
        return self._http

    def _rate_limit(self) -> None:
        """Enforce minimum interval between API calls."""
        elapsed = time.monotonic() - self._last_call_time
        if elapsed < config.MIN_CALL_INTERVAL_SEC:
            time.sleep(config.MIN_CALL_INTERVAL_SEC - elapsed)

    def _build_params(
        self,
        keywords: str,
        operation_name: str | None = None,
        category_id: int | None = None,
        page_number: int = 1,
        entries_per_page: int | None = None,
    ) -> dict[str, str]:
        """Construct the query-string params for a Finding API call."""
        params: dict[str, str] = {
            "OPERATION-NAME": operation_name or config.OPERATION_SEARCH,
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self._app_id,
            "RESPONSE-DATA-FORMAT": "XML",
            "REST-PAYLOAD": "",
            "keywords": keywords,
            "paginationInput.entriesPerPage": str(
                entries_per_page or config.PAGE_SIZE
            ),
            "paginationInput.pageNumber": str(page_number),
        }
        if category_id is not None:
            params["categoryId"] = str(category_id)
        return params

    def _call_api(
        self,
        keywords: str,
        operation_name: str | None = None,
        category_id: int | None = None,
        page_number: int = 1,
    ) -> str:
        """Make a single API call with retry+backoff. Returns XML body string."""
        params = self._build_params(
            keywords=keywords,
            operation_name=operation_name,
            category_id=category_id,
            page_number=page_number,
        )

        last_exception: Exception | None = None
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                self._rate_limit()
                self._last_call_time = time.monotonic()

                url = f"{self._endpoint}?{urlencode(params)}"
                logger.debug("eBay API call: %s …", url[:120])

                resp = self._client.get(url)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in config.RETRYABLE_STATUS_CODES:
                    logger.warning(
                        "eBay API returned %d (attempt %d/%d)",
                        resp.status_code,
                        attempt + 1,
                        config.MAX_RETRIES + 1,
                    )
                else:
                    # Non-retryable error — raise immediately
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

        # All retries exhausted
        raise last_exception or RuntimeError("eBay API call failed after all retries")

    def _parse_response(self, xml_body: str) -> ET.Element:
        """Parse the XML response, raising on eBay error."""
        root = ET.fromstring(xml_body)

        # Check for eBay-level errors
        ack = root.attrib.get("ack", "")
        if ack == "Failure":
            errors = root.findall(f".//{_ns('errorMessage')}/{_ns('error')}")
            messages = []
            for e in errors:
                msg = _text(e.find(_ns("message")))
                messages.append(msg)
            error_str = "; ".join(messages) if messages else "Unknown eBay API error"
            raise EBayAPIError(error_str, root)

        if ack == "PartialFailure":
            logger.warning("eBay API returned PartialFailure — some items may be missing")

        return root

    def _parse_search_items(
        self,
        root: ET.Element,
        keywords: str,
        category_id: int | None,
        page_number: int,
    ) -> SearchResult:
        """Parse <findItemsByKeywordsResponse> or <findCompletedItemsResponse>."""
        search_result_el = root.find(_ns("searchResult"))
        if search_result_el is None:
            logger.warning("No searchResult element in response")
            return SearchResult(
                items=[],
                total_entries=0,
                page_number=page_number,
                entries_per_page=config.PAGE_SIZE,
                query_keywords=keywords,
                category_id=category_id,
            )

        total_str = search_result_el.attrib.get("count", "0")
        total = int(total_str) if total_str.isdigit() else 0
        items: list[EBayListing] = []
        for item_el in search_result_el.findall(_ns("item")):
            try:
                items.append(_parse_listing(item_el))
            except Exception:
                logger.exception("Failed to parse an item element; skipping")

        return SearchResult(
            items=items,
            total_entries=total,
            page_number=page_number,
            entries_per_page=config.PAGE_SIZE,
            query_keywords=keywords,
            category_id=category_id,
        )

    # ── Public API ───────────────────────────────────────────────────

    def search_items(
        self,
        keywords: str,
        category_id: int | None = None,
        limit: int | None = None,
        max_pages: int | None = None,
    ) -> SearchResult:
        """
        Search active eBay listings.

        Args:
            keywords: Search keywords (required by eBay Finding API).
            category_id: Optional eBay category ID to filter by.
            limit: Max total items to return (aggregates across pages).
            max_pages: Max pages to fetch (defaults to config.MAX_PAGES_PER_CATEGORY).

        Returns:
            SearchResult with combined items from all fetched pages.
        """
        pages_limit = max_pages if max_pages is not None else config.MAX_PAGES_PER_CATEGORY
        items_limit = limit or pages_limit * config.PAGE_SIZE

        all_items: list[EBayListing] = []
        page = 1

        while page <= pages_limit:
            xml_body = self._call_api(
                keywords=keywords,
                operation_name=config.OPERATION_SEARCH,
                category_id=category_id,
                page_number=page,
            )
            root = self._parse_response(xml_body)
            result = self._parse_search_items(root, keywords, category_id, page)

            all_items.extend(result.items)
            logger.info(
                "Category %s: page %d → %d items (total so far: %d)",
                category_id or "all",
                page,
                len(result.items),
                len(all_items),
            )

            # Stop if we've hit the desired limit or exhausted results
            if len(all_items) >= items_limit:
                break
            if len(result.items) < config.PAGE_SIZE:
                # Last page — no more results
                break
            if result.total_entries and len(all_items) >= result.total_entries:
                break

            page += 1

        # Trim to exact limit if needed
        if items_limit and len(all_items) > items_limit:
            all_items = all_items[:items_limit]

        return SearchResult(
            items=all_items,
            total_entries=len(all_items),
            page_number=1,
            entries_per_page=config.PAGE_SIZE,
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

        Args:
            keywords: Search keywords.
            category_id: Optional eBay category ID.
            limit: Max total items.

        Returns:
            SearchResult with completed listing items.
        """
        items_limit = limit or config.PAGE_SIZE * 2  # Default: 2 pages

        all_items: list[EBayListing] = []
        page = 1

        while True:
            xml_body = self._call_api(
                keywords=keywords,
                operation_name=config.OPERATION_COMPLETED,
                category_id=category_id,
                page_number=page,
            )
            root = self._parse_response(xml_body)
            result = self._parse_search_items(root, keywords, category_id, page)

            all_items.extend(result.items)
            logger.info(
                "Completed items cat %s p%d: %d items",
                category_id or "all",
                page,
                len(result.items),
            )

            if len(all_items) >= items_limit:
                break
            if len(result.items) < config.PAGE_SIZE:
                break
            if result.total_entries and len(all_items) >= result.total_entries:
                break
            page += 1

        if items_limit and len(all_items) > items_limit:
            all_items = all_items[:items_limit]

        return SearchResult(
            items=all_items,
            total_entries=len(all_items),
            page_number=1,
            entries_per_page=config.PAGE_SIZE,
            query_keywords=keywords,
            category_id=category_id,
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
    """Raised when the eBay API returns an error (ack=Failure)."""

    def __init__(self, message: str, raw_xml: ET.Element | None = None) -> None:
        super().__init__(message)
        self.raw_xml = raw_xml
