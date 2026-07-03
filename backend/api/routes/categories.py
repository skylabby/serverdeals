"""
Category routes — list all categories with current listing counts.

Degrades gracefully to empty list when DB is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.api.models.schemas import CategoryOut
from backend.db.models import Category, Listing, ModelStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    db: Optional[AsyncSession] = Depends(get_db),
) -> list[CategoryOut]:
    """
    Return all categories with current listing counts and latest median prices.
    """
    if db is None:
        return []

    try:
        # Subquery: latest stats per category
        latest_stats_subq = (
            select(
                ModelStats.category_key,
                func.max(ModelStats.date).label("max_date"),
            )
            .group_by(ModelStats.category_key)
            .subquery()
        )

        latest_stats_q = select(
            ModelStats.category_key,
            ModelStats.median_price,
        ).join(
            latest_stats_subq,
            (ModelStats.category_key == latest_stats_subq.c.category_key)
            & (ModelStats.date == latest_stats_subq.c.max_date),
        )
        stats_result = (await db.execute(latest_stats_q)).all()
        median_map: dict[str, Optional[float]] = {
            row.category_key: float(row.median_price) if row.median_price is not None else None
            for row in stats_result
        }

        # Count listings per category
        count_q = (
            select(
                Listing.category_key,
                func.count(Listing.id).label("cnt"),
            )
            .group_by(Listing.category_key)
        )
        count_rows = (await db.execute(count_q)).all()
        count_map: dict[str, int] = {
            row.category_key: row.cnt for row in count_rows
        }

        # Fetch all categories
        cats = (
            (await db.execute(
                select(Category).order_by(Category.group_key, Category.display_name)
            ))
            .scalars()
            .all()
        )

        return [
            CategoryOut(
                key=c.key,
                display_name=c.display_name,
                group_key=c.group_key,
                listing_count=count_map.get(c.key, 0),
                median_price=median_map.get(c.key),
            )
            for c in cats
        ]
    except Exception:
        logger.exception("Failed to query categories — returning empty")
        return []
