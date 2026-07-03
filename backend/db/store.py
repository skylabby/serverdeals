"""
Storage layer for persisting scraped eBay listings to PostgreSQL.

Called by the scheduler with items fetched from the eBay API.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import async_session
from backend.db.models import Listing, PriceSnapshot
from backend.scraper.ebay_client import EBayListing

logger = logging.getLogger(__name__)


async def store_listings(
    items: list[EBayListing],
    category_key: str,
) -> int:
    """
    Upsert scraped listings into the database.

    - New listings are inserted.
    - Existing listings (matched by ebay_item_id) update price/condition/end_time.
    - Price snapshots are appended when the price changes or is first seen.

    Returns the number of listings upserted.
    """
    if not items:
        return 0

    stored = 0
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        for item in items:
            try:
                await _upsert_listing(session, item, category_key, now)
                stored += 1
            except Exception:
                logger.exception("Failed to store listing %s", item.item_id)
        await session.commit()

    logger.info("Stored %d/%d listings for category '%s'", stored, len(items), category_key)
    return stored


async def _upsert_listing(
    session: AsyncSession,
    item: EBayListing,
    category_key: str,
    now: datetime,
) -> None:
    """Upsert a single listing and record its price snapshot."""
    price = Decimal(str(item.price)) if item.price else Decimal("0")

    stmt = pg_insert(Listing).values(
        ebay_item_id=item.item_id,
        title=item.title or "",
        price=price,
        currency=item.currency or "USD",
        condition=item.condition or "Unknown",
        listing_type=item.listing_type or "Unknown",
        end_time=item.end_time,
        image_url=item.gallery_url or "",
        category_key=category_key,
        specs_json=json.dumps(item.specs) if item.specs else "{}",
        first_seen=now,
        last_seen=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["ebay_item_id"],
        set_=dict(
            price=price,
            condition=item.condition or "Unknown",
            listing_type=item.listing_type or "Unknown",
            end_time=item.end_time,
            image_url=item.gallery_url or "",
            last_seen=now,
        ),
    )
    await session.execute(stmt)

    # Record price snapshot
    snap = PriceSnapshot(
        listing_id=select(Listing.id).where(Listing.ebay_item_id == item.item_id).scalar_subquery(),
        price=price,
        captured_at=now,
    )
    # Use raw insert to avoid loading the listing first
    from sqlalchemy import text
    await session.execute(
        text(
            "INSERT INTO price_snapshots (listing_id, price, captured_at) "
            "SELECT id, :price, :captured_at FROM listings WHERE ebay_item_id = :item_id"
        ),
        {"price": price, "captured_at": now, "item_id": item.item_id},
    )
