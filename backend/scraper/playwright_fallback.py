"""
Playwright-based eBay scraper fallback.

When the eBay Finding API returns insufficient results (sandbox sparsity)
or fails entirely, this module scrapes eBay search pages directly via
headless browser. Inspired by changedetection.io's visual scraping approach.

Usage:
    fallback = EBayPlaywrightFallback()
    listings = await fallback.search("Dell PowerEdge server", max_items=50)
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Only import playwright when actually needed (optional dependency)
try:
    from playwright.async_api import async_playwright, Browser, Page

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright not installed. Install with: pip install playwright && playwright install chromium"
    )


@dataclass
class ScrapedListing:
    """A listing scraped from an eBay search results page."""

    title: str
    price: float
    currency: str
    condition: str
    listing_type: str
    item_url: str
    image_url: str
    item_id: str = ""


EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"


class EBayPlaywrightFallback:
    """Scrape eBay search results using Playwright headless browser."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        if not _PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is not installed. Run: pip install playwright && playwright install chromium"
            )
        self._headless = headless
        self._timeout = timeout
        self._browser: Browser | None = None
        self._playwright = None

    async def _ensure_browser(self) -> Browser:
        """Lazy-init the Playwright browser."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
        return self._browser

    async def search(
        self,
        keywords: str,
        max_items: int = 50,
        category_id: int | None = None,
    ) -> list[ScrapedListing]:
        """
        Search eBay and return scraped listings.

        Falls back gracefully if Playwright isn't available.
        """
        browser = await self._ensure_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        try:
            # Build search URL
            params = {
                "_nkw": keywords,
                "_ipg": min(max_items, 240),  # items per page (max 240)
                "LH_Sold": "1",  # show sold items for price data
                "rt": "nc",
            }
            if category_id:
                params["_sacat"] = str(category_id)

            query_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{EBAY_SEARCH_URL}?{query_str}"
            logger.info("Playwright fallback: navigating to %s …", url[:100])

            await page.goto(url, wait_until="domcontentloaded", timeout=self._timeout)

            # Wait for results to load
            await page.wait_for_selector(
                "ul.srp-results li.s-item, div.s-item", timeout=15000
            )

            listings = await self._extract_listings(page, max_items)
            logger.info("Playwright fallback: scraped %d listings", len(listings))
            return listings

        except Exception as exc:
            logger.warning("Playwright fallback failed: %s", exc)
            return []
        finally:
            await context.close()

    @staticmethod
    async def _extract_listings(
        page: Page, max_items: int
    ) -> list[ScrapedListing]:
        """Extract listing data from the loaded eBay results page."""
        items = await page.query_selector_all("li.s-item, div.s-item")
        listings: list[ScrapedListing] = []

        for item_el in items[:max_items]:
            try:
                # Title
                title_el = await item_el.query_selector(".s-item__title, h3.s-item__title")
                title = (await title_el.inner_text()).strip() if title_el else ""

                # Skip "Shop on eBay" banner rows
                if not title or "shop on ebay" in title.lower():
                    continue

                # Price
                price_el = await item_el.query_selector(".s-item__price")
                price_text = (await price_el.inner_text()).strip() if price_el else "$0"
                price, currency = EBayPlaywrightFallback._parse_price(price_text)

                # Image
                img_el = await item_el.query_selector("img.s-item__image-img")
                image_url = (
                    await img_el.get_attribute("src") if img_el else ""
                ) or ""

                # URL
                link_el = await item_el.query_selector("a.s-item__link")
                item_url = (
                    await link_el.get_attribute("href") if link_el else ""
                ) or ""

                # Item ID from URL
                item_id = ""
                if item_url:
                    m = re.search(r"/itm/(\d+)", item_url)
                    if m:
                        item_id = m.group(1)

                # Condition and listing type
                subtitle_el = await item_el.query_selector(
                    ".s-item__subtitle, .SECONDARY_INFO"
                )
                subtitle = (
                    (await subtitle_el.inner_text()).strip() if subtitle_el else ""
                )
                condition = "Used"
                listing_type = "FixedPrice"
                if "new" in subtitle.lower():
                    condition = "New"
                elif "refurbished" in subtitle.lower():
                    condition = "Refurbished"

                listings.append(
                    ScrapedListing(
                        title=title,
                        price=price,
                        currency=currency,
                        condition=condition,
                        listing_type=listing_type,
                        item_url=item_url,
                        image_url=image_url,
                        item_id=item_id,
                    )
                )
            except Exception:
                logger.debug("Failed to extract a listing row; skipping")

        return listings

    @staticmethod
    def _parse_price(text: str) -> tuple[float, str]:
        """Parse eBay price text like '$1,234.56' or '$45.00 to $67.00'."""
        text = text.strip().replace(",", "")
        # Handle price ranges — take the lower bound
        if " to " in text:
            text = text.split(" to ")[0].strip()
        # Extract numeric value
        m = re.search(r"\$?\s*([\d.]+)", text)
        if m:
            return float(m.group(1)), "USD"
        return 0.0, "USD"

    async def close(self) -> None:
        """Close the browser and playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


async def fallback_search(
    keywords: str,
    category_id: int | None = None,
    max_items: int = 50,
) -> list[ScrapedListing]:
    """
    Convenience async function: search eBay with Playwright fallback.

    Returns empty list if Playwright is not installed or the scrape fails.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available — skipping fallback search")
        return []

    fallback = EBayPlaywrightFallback()
    try:
        return await fallback.search(
            keywords=keywords,
            max_items=max_items,
            category_id=category_id,
        )
    finally:
        await fallback.close()
