"""
APScheduler-based cron job that scrapes all eBay server hardware categories
every 3 hours and stores results in the database.

Standalone entry point:
    python -m backend.scraper.scheduler
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .categories import CATEGORIES
from .ebay_client import EBayClient

try:
    from backend.db.store import store_listings
    _DB_AVAILABLE = True
except ImportError:
    store_listings = None
    _DB_AVAILABLE = False

logger = logging.getLogger(__name__)


# ── Scrape logic ─────────────────────────────────────────────────────────


def scrape_all_categories(
    client: EBayClient | None = None,
    store_callback: callable | None = None,
) -> dict[str, int]:
    """
    Iterate all 25 categories, fetch active listings, and store results.

    Args:
        client: Optional pre-constructed EBayClient (injected for testing).
        store_callback: Optional fn(items, category) called to persist results.
                        Signature: store_callback(items: list, category: EBayCategory) -> int

    Returns:
        Dict mapping "total" and per-category names to item counts.
    """
    _client = client or EBayClient()
    stats: dict[str, int] = {"total": 0}
    own_client = client is None

    try:
        total_cats = len(CATEGORIES)
        for idx, category in enumerate(CATEGORIES, start=1):
            logger.info(
                "[%d/%d] Scraping category %d: %s",
                idx,
                total_cats,
                category.ebay_category_id,
                category.display_name,
            )
            try:
                keywords = category.ebay_search_query
                result = _client.search_items(
                    keywords=keywords,
                    category_id=category.ebay_category_id,
                )
                count = len(result.items)
                stats[category.display_name] = count
                stats["total"] += count

                logger.info(
                    "  → %d items fetched for '%s' (cat %d)",
                    count,
                    category.display_name,
                    category.ebay_category_id,
                )

                if store_callback and result.items:
                    try:
                        stored = store_callback(result.items, category)
                        logger.debug("  Stored %d items via callback", stored)
                    except Exception:
                        logger.exception("Store callback failed for category %d", category.ebay_category_id)

            except Exception:
                logger.exception(
                    "Error scraping category %d (%s)",
                    category.ebay_category_id,
                    category.display_name,
                )
                stats.setdefault(category.display_name, 0)  # mark as attempted

    finally:
        if own_client:
            _client.close()

    return stats


def run_once() -> dict[str, int]:
    """One-shot scrape: called on startup and by the cron trigger."""
    logger.info("=== Starting eBay scrape cycle at %s ===", datetime.now(timezone.utc).isoformat())
    start = time.monotonic()

    import asyncio

    async def _store_callback(items, category):
        if _DB_AVAILABLE and store_listings:
            return await store_listings(items, category.key)
        return 0

    stats = scrape_all_categories(
        store_callback=lambda items, cat: asyncio.run(_store_callback(items, cat))
    )

    elapsed = time.monotonic() - start
    logger.info(
        "=== Scrape complete: %d items across %d categories in %.1fs ===",
        stats["total"],
        len(stats) - 1,  # minus the 'total' key
        elapsed,
    )
    return stats


# ── Scheduler entry point ───────────────────────────────────────────────


def main() -> None:
    """Entry point for `python -m backend.scraper.scheduler`."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format=config.LOG_FORMAT,
        stream=sys.stdout,
    )
    # Quiet httpx's own logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    logger.info("ServerDeals scraper scheduler starting…")
    logger.info("Schedule: %s", config.SCRAPE_CRON_SCHEDULE)
    logger.info("Categories: %d", len(CATEGORIES))

    scheduler = BackgroundScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_once,
        trigger=CronTrigger.from_crontab(config.SCRAPE_CRON_SCHEDULE),
        id="scrape_ebay",
        name="Scrape all eBay server categories",
        replace_existing=True,
    )
    scheduler.start()

    # Optional immediate run on startup
    if config.SCRAPE_ON_STARTUP:
        logger.info("Running initial scrape on startup…")
        run_once()

    try:
        # Keep the scheduler alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler…")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
