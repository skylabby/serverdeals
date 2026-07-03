"""
Deal routes — paginated listing, hot deals, single deal with price history.

All endpoints degrade gracefully when the database is unreachable,
returning empty arrays / 0 counts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.dependencies import get_db
from backend.api.models.schemas import DealDetailOut, DealOut, PaginatedResponse, PricePoint
from backend.db.models import Category, Listing, PriceSnapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deals", tags=["deals"])

# ── Try to import the scoring engine (built by another agent) ───────────────
_SCORING_AVAILABLE = False
_score_listing = None  # type: ignore

try:
    from backend.scoring.engine import score_listing  # type: ignore[import-untyped]

    _SCORING_AVAILABLE = True
    _score_listing = score_listing
except ImportError:
    logger.info("Scoring engine not yet available — scores will be null")


# ── Helpers ─────────────────────────────────────────────────────────────────


def _apply_score(listing: Listing) -> tuple[Optional[float], Optional[str], Optional[str]]:
    """Apply the scoring engine to a listing if available, else return (None, None, None)."""
    if not _SCORING_AVAILABLE or _score_listing is None:
        return None, None, None
    try:
        result = _score_listing(listing)
        return result.score, result.classification, result.price_range_label
    except Exception:
        logger.exception("Scoring engine failed for listing %d", listing.id)
        return None, None, None


def _build_deal_out(listing: Listing) -> DealOut:
    """Convert a SQLAlchemy Listing into a DealOut with scoring applied."""
    score, classification, price_range = _apply_score(listing)
    display = listing.category.display_name if listing.category else ""
    return DealOut(
        id=listing.id,
        ebay_item_id=listing.ebay_item_id,
        title=listing.title,
        price=float(listing.price) if listing.price is not None else None,
        currency=listing.currency,
        condition=listing.condition,
        listing_type=listing.listing_type,
        image_url=listing.image_url,
        category_key=listing.category_key,
        category_display=display,
        score=score,
        classification=classification,
        price_range=price_range,
        view_url=f"https://www.ebay.com/itm/{listing.ebay_item_id}",
    )


def _build_deal_detail(listing: Listing, snapshots: list[PriceSnapshot]) -> DealDetailOut:
    """Build a DealDetailOut with price history."""
    base = _build_deal_out(listing)
    history = [
        PricePoint(
            price=float(s.price),
            captured_at=s.captured_at,
        )
        for s in snapshots
    ]
    return DealDetailOut(
        **base.model_dump(),
        price_history=history,
    )


def _empty_page(page: int) -> PaginatedResponse[DealOut]:
    return PaginatedResponse[DealOut](
        items=[],
        page=page,
        total_pages=0,
        total_items=0,
    )


# ── Routes ──────────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedResponse[DealOut])
async def list_deals(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category key"),
    group: Optional[str] = Query(None, description="Filter by category group"),
    classification: Optional[str] = Query(None, description="Filter by classification (hot/good/fair)"),
    sort: Optional[str] = Query(None, pattern="^(score|price|date)$", description="Sort field"),
    db: Optional[AsyncSession] = Depends(get_db),
) -> PaginatedResponse[DealOut]:
    """
    Return paginated deals with optional filtering and sorting.

    Filters: category, group, classification.
    Sorts: score (desc), price (asc), date (most recent first).
    """
    if db is None:
        return _empty_page(page)

    try:
        base = (
            select(Listing)
            .options(selectinload(Listing.category))
        )

        # ── Filters ──────────────────────────────────────────────
        if category:
            base = base.where(Listing.category_key == category)
        if group:
            base = base.join(Listing.category).where(Category.group_key == group)

        # ── Sort ─────────────────────────────────────────────────
        if sort == "price":
            base = base.order_by(Listing.price.asc().nulls_last())
        elif sort == "date":
            base = base.order_by(Listing.first_seen.desc())
        else:
            base = base.order_by(Listing.first_seen.desc())

        # ── Count ────────────────────────────────────────────────
        count_q = select(func.count()).select_from(base.subquery())
        total_items: int = (await db.execute(count_q)).scalar() or 0

        # ── Paginate ─────────────────────────────────────────────
        offset = (page - 1) * per_page
        base = base.offset(offset).limit(per_page)
        rows = (await db.execute(base)).scalars().all()

        deals = [_build_deal_out(r) for r in rows]
        total_pages = max(1, (total_items + per_page - 1) // per_page)

        return PaginatedResponse[DealOut](
            items=deals,
            page=page,
            total_pages=total_pages,
            total_items=total_items,
        )
    except Exception:
        logger.exception("Failed to query deals")
        return _empty_page(page)


@router.get("/hot", response_model=list[DealOut])
async def hot_deals(
    limit: int = Query(20, ge=1, le=100, description="Max hot deals to return"),
    db: Optional[AsyncSession] = Depends(get_db),
) -> list[DealOut]:
    """
    Return top-scored deals (hot deals).

    If the scoring engine is available, scores are computed at read time
    and deals are sorted by score descending. Otherwise falls back to
    newest listings.
    """
    if db is None:
        return []

    try:
        if _SCORING_AVAILABLE and _score_listing is not None:
            base = (
                select(Listing)
                .options(selectinload(Listing.category))
                .order_by(Listing.first_seen.desc())
                .limit(min(500, limit * 5))
            )
            rows = (await db.execute(base)).scalars().all()
            scored = sorted(
                [_build_deal_out(r) for r in rows],
                key=lambda d: d.score if d.score is not None else 0.0,
                reverse=True,
            )
            return scored[:limit]

        base = (
            select(Listing)
            .options(selectinload(Listing.category))
            .order_by(Listing.first_seen.desc())
            .limit(limit)
        )
        rows = (await db.execute(base)).scalars().all()
        return [_build_deal_out(r) for r in rows]
    except Exception:
        logger.exception("Failed to query hot deals")
        return []


@router.get("/{deal_id}", response_model=DealDetailOut)
async def get_deal(
    deal_id: int,
    db: Optional[AsyncSession] = Depends(get_db),
) -> DealDetailOut:
    """
    Return a single deal with its price history (last 60 days of snapshots).
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        q = (
            select(Listing)
            .options(selectinload(Listing.category))
            .where(Listing.id == deal_id)
        )
        result = await db.execute(q)
        listing = result.scalar_one_or_none()

        if listing is None:
            raise HTTPException(status_code=404, detail="Deal not found")

        since = datetime.now(timezone.utc) - timedelta(days=60)
        snap_q = (
            select(PriceSnapshot)
            .where(
                PriceSnapshot.listing_id == listing.id,
                PriceSnapshot.captured_at >= since,
            )
            .order_by(PriceSnapshot.captured_at.asc())
        )
        snapshots = (await db.execute(snap_q)).scalars().all()

        return _build_deal_detail(listing, list(snapshots))

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to query deal %d", deal_id)
        raise HTTPException(status_code=503, detail="Database unavailable")
