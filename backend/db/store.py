"""
Synchronous storage for persisting scraped eBay listings to PostgreSQL.

Uses the synchronous DATABASE_URL (psycopg2) to avoid asyncio event-loop issues.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from backend.scraper.categories import CATEGORIES, CategoryDef
from backend.scraper.ebay_client import EBayListing

load_dotenv()

logger = logging.getLogger(__name__)

# Sync DATABASE_URL — replace asyncpg with psycopg2
_SYNC_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql+asyncpg://", "postgresql://"
).replace("postgresql://", "postgresql://")


def _get_conn():
    return psycopg2.connect(_SYNC_URL)


def seed_categories() -> int:
    """Insert all 25 categories. Returns count inserted."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            count = 0
            for cat in CATEGORIES:
                cur.execute(
                    """INSERT INTO categories (key, display_name, ebay_search_query, group_key, ebay_category_id)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (key) DO UPDATE SET
                         display_name = EXCLUDED.display_name,
                         ebay_search_query = EXCLUDED.ebay_search_query,
                         group_key = EXCLUDED.group_key,
                         ebay_category_id = EXCLUDED.ebay_category_id""",
                    (cat.key, cat.display_name, cat.ebay_search_query, cat.group_key, cat.ebay_category_id),
                )
                count += 1
            conn.commit()
            logger.info("Seeded %d categories", count)
            return count
    finally:
        conn.close()


def store_listings(items: list[EBayListing], category: CategoryDef) -> int:
    """Upsert listings and record price snapshots. Returns count stored."""
    if not items:
        return 0

    conn = _get_conn()
    now = datetime.now(timezone.utc)
    stored = 0

    try:
        with conn.cursor() as cur:
            for item in items:
                try:
                    price = Decimal(str(item.current_price)) if item.current_price else Decimal("0")
                    specs = "{}"
                    if hasattr(item, 'specs') and item.specs:
                        specs = json.dumps(item.specs)

                    cur.execute(
                        """INSERT INTO listings 
                           (ebay_item_id, title, price, currency, condition, listing_type, 
                            end_time, image_url, category_key, specs_json, first_seen, last_seen)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (ebay_item_id) DO UPDATE SET
                             price = EXCLUDED.price,
                             condition = EXCLUDED.condition,
                             listing_type = EXCLUDED.listing_type,
                             end_time = EXCLUDED.end_time,
                             image_url = EXCLUDED.image_url,
                             last_seen = EXCLUDED.last_seen""",
                        (
                            item.item_id, item.title or "", price, item.currency_id or "USD",
                            item.condition or "Unknown", item.listing_type or "Unknown",
                            item.end_time, item.gallery_url or "", category.key,
                            specs, now, now,
                        ),
                    )

                    # Record price snapshot
                    cur.execute(
                        """INSERT INTO price_snapshots (listing_id, price, captured_at)
                           SELECT id, %s, %s FROM listings WHERE ebay_item_id = %s""",
                        (price, now, item.item_id),
                    )

                    stored += 1
                except Exception:
                    logger.exception("Failed to store listing %s", item.item_id)

            conn.commit()
            logger.info("Stored %d/%d listings for '%s'", stored, len(items), category.display_name)
    finally:
        conn.close()

    return stored
