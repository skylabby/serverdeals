"""
Stats routes — live counters for the dashboard.

Returns total listings, hot/good deal counts, category count, and last updated.
Degrades gracefully to zeros when DB is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.api.models.schemas import StatsOut
from backend.db.models import Category, Listing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats(
    db: Optional[AsyncSession] = Depends(get_db),
) -> StatsOut:
    """
    Return live stats: total listings, categories, hot/good deal counts, last updated.
    """
    if db is None:
        return StatsOut()

    try:
        total_listings_q = select(func.count(Listing.id))
        total_listings: int = (await db.execute(total_listings_q)).scalar() or 0

        total_categories_q = select(func.count(Category.id))
        total_categories: int = (await db.execute(total_categories_q)).scalar() or 0

        last_updated_q = select(func.max(Listing.first_seen))
        last_updated = (await db.execute(last_updated_q)).scalar()

        hot_count = 0
        good_count = 0

        if total_listings > 0:
            hot_threshold_q = select(
                func.percentile_disc(0.05).within_group(Listing.price.asc())
            ).where(Listing.price.isnot(None))
            good_threshold_q = select(
                func.percentile_disc(0.20).within_group(Listing.price.asc())
            ).where(Listing.price.isnot(None))

            hot_threshold = (await db.execute(hot_threshold_q)).scalar()
            good_threshold = (await db.execute(good_threshold_q)).scalar()

            if hot_threshold is not None:
                hot_count_q = select(func.count(Listing.id)).where(
                    Listing.price.isnot(None),
                    Listing.price <= hot_threshold,
                )
                hot_count = (await db.execute(hot_count_q)).scalar() or 0

            if good_threshold is not None:
                good_count_q = select(func.count(Listing.id)).where(
                    Listing.price.isnot(None),
                    Listing.price <= good_threshold,
                )
                good_count = (await db.execute(good_count_q)).scalar() or 0

        return StatsOut(
            total_listings=total_listings,
            total_categories=total_categories,
            hot_deals_count=hot_count,
            good_deals_count=good_count,
            last_updated=last_updated,
        )
    except Exception:
        logger.exception("Failed to query stats — returning zeros")
        return StatsOut()
