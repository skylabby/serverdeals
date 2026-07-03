"""
Deal scoring engine for ServerDeals.

Computes deal scores based on 60-day rolling median prices per category,
classifies deals as Hot/Good/Fair/NoData, computes daily model_stats,
and surfaces top deals and price ranges.

Usage:
    from backend.db.database import AsyncSessionLocal
    from backend.scoring.engine import DealScoringEngine

    async with AsyncSessionLocal() as session:
        engine = DealScoringEngine(session)
        scores = await engine.compute_scores()
        top_deal = await engine.get_top_deal()
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Listing, ModelStats, PriceSnapshot

logger = logging.getLogger(__name__)


class DealScoringEngine:
    """Async engine that scores listings against 60-day rolling median prices.

    Scoring formula:  Score = (1 − current_price / median) × 100
    *  Positive score → price is below median (a deal).
    *  Negative score → price is above median.

    Classifications:
        Hot    ≥ 40 % below median
        Good   20–39 % below median
        Fair   0–19 % below median
        NoData  no price history available for this category

    All public methods are async and accept/return plain dicts for easy
    JSON serialisation.
    """

    HOT_THRESHOLD: float = 40.0
    GOOD_THRESHOLD: float = 20.0
    FAIR_THRESHOLD: float = 0.0

    # ------------------------------------------------------------------
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Helpers ──────────────────────────────────────────────────────
    async def _get_60_day_medians(self) -> dict[str, Decimal]:
        """Return {category_key: median_price} for all snapshots in the
        past 60 days, computed with PostgreSQL ``percentile_cont(0.5)``."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=60)

        stmt = (
            select(
                Listing.category_key,
                func.percentile_cont(0.5)
                .within_group(PriceSnapshot.price)
                .label("median"),
            )
            .join(PriceSnapshot, Listing.id == PriceSnapshot.listing_id)
            .where(PriceSnapshot.captured_at >= cutoff)
            .group_by(Listing.category_key)
        )
        result = await self.session.execute(stmt)
        return {row.category_key: row.median for row in result if row.median is not None}

    @staticmethod
    def _classify(score: float | None) -> str:
        if score is None:
            return "NoData"
        if score >= DealScoringEngine.HOT_THRESHOLD:
            return "Hot"
        if score >= DealScoringEngine.GOOD_THRESHOLD:
            return "Good"
        if score >= DealScoringEngine.FAIR_THRESHOLD:
            return "Fair"
        return "Fair"  # negative score is still "Fair" — just not a good deal

    # ── Public API ───────────────────────────────────────────────────

    async def compute_scores(self) -> list[dict[str, Any]]:
        """Score every listing that has a non-null *price* against its
        category's 60-day median.

        Returns a list of dicts sorted by score descending (best deals first).
        """
        medians = await self._get_60_day_medians()

        stmt = select(Listing).where(Listing.price.isnot(None))
        result = await self.session.execute(stmt)
        listings = result.scalars().all()

        scored: list[dict[str, Any]] = []
        for listing in listings:
            price = listing.price
            median = medians.get(listing.category_key)

            if price is None or median is None or median == 0:
                scored.append(
                    {
                        "listing_id": listing.id,
                        "ebay_item_id": listing.ebay_item_id,
                        "title": listing.title,
                        "category_key": listing.category_key,
                        "price": float(price) if price else None,
                        "median_60d": None,
                        "score": None,
                        "classification": "NoData",
                    }
                )
                continue

            price_f = float(price)
            median_f = float(median)
            score = round((1.0 - price_f / median_f) * 100.0, 2)

            scored.append(
                {
                    "listing_id": listing.id,
                    "ebay_item_id": listing.ebay_item_id,
                    "title": listing.title,
                    "category_key": listing.category_key,
                    "price": price_f,
                    "median_60d": median_f,
                    "score": score,
                    "classification": self._classify(score),
                }
            )

        scored.sort(
            key=lambda x: x["score"] if x["score"] is not None else float("-inf"),
            reverse=True,
        )
        return scored

    async def compute_model_stats(self) -> dict[str, dict[str, Any]]:
        """Calculate per-category stats from today's listings (median, min,
        max, count) and upsert them into the ``model_stats`` table.

        Returns {category_key: {median_price, min_price, max_price, listing_count}}.
        """
        today = date.today()

        stmt = (
            select(
                Listing.category_key,
                func.percentile_cont(0.5)
                .within_group(Listing.price)
                .label("median_price"),
                func.min(Listing.price).label("min_price"),
                func.max(Listing.price).label("max_price"),
                func.count(Listing.id).label("listing_count"),
            )
            .where(Listing.price.isnot(None))
            .group_by(Listing.category_key)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        stats: dict[str, dict[str, Any]] = {}
        for row in rows:
            cat_key: str = row.category_key
            cat_stats = {
                "median_price": float(row.median_price) if row.median_price else None,
                "min_price": float(row.min_price) if row.min_price else None,
                "max_price": float(row.max_price) if row.max_price else None,
                "listing_count": row.listing_count,
            }
            stats[cat_key] = cat_stats

            # Upsert — one row per (category_key, date)
            existing = await self.session.execute(
                select(ModelStats).where(
                    and_(ModelStats.category_key == cat_key, ModelStats.date == today)
                )
            )
            model_stat = existing.scalar_one_or_none()

            if model_stat is not None:
                model_stat.median_price = row.median_price
                model_stat.min_price = row.min_price
                model_stat.max_price = row.max_price
                model_stat.listing_count = row.listing_count
            else:
                model_stat = ModelStats(
                    category_key=cat_key,
                    date=today,
                    median_price=row.median_price,
                    min_price=row.min_price,
                    max_price=row.max_price,
                    listing_count=row.listing_count or 0,
                )
                self.session.add(model_stat)

        await self.session.commit()
        logger.info("compute_model_stats: upserted stats for %d categories", len(stats))
        return stats

    async def get_top_deal(self) -> dict[str, Any] | None:
        """Return the single best-scored listing from the past 24 hours.

        The "past 24h" window is based on ``first_seen`` — only listings
        first discovered within the last day are considered.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        medians = await self._get_60_day_medians()

        stmt = select(Listing).where(
            and_(Listing.price.isnot(None), Listing.first_seen >= cutoff)
        )
        result = await self.session.execute(stmt)
        listings = result.scalars().all()

        best: dict[str, Any] | None = None
        best_score = float("-inf")

        for listing in listings:
            median = medians.get(listing.category_key)
            price = listing.price

            if price is None or median is None or median == 0:
                continue

            price_f = float(price)
            median_f = float(median)
            score = round((1.0 - price_f / median_f) * 100.0, 2)

            if score > best_score:
                best_score = score
                best = {
                    "listing_id": listing.id,
                    "ebay_item_id": listing.ebay_item_id,
                    "title": listing.title,
                    "category_key": listing.category_key,
                    "price": price_f,
                    "median_60d": median_f,
                    "score": score,
                    "classification": self._classify(score),
                }

        return best

    async def get_price_range(self, category_key: str) -> dict[str, Any] | None:
        """Return the latest {min, median, max} for *category_key* from
        the ``model_stats`` table.

        Looks for the most recent date entry since data may not exist
        for today if no listings have been scraped yet.
        """
        stmt = (
            select(ModelStats)
            .where(ModelStats.category_key == category_key)
            .order_by(ModelStats.date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        stat = result.scalar_one_or_none()

        if stat is None:
            return None

        return {
            "category_key": stat.category_key,
            "date": stat.date.isoformat(),
            "min": float(stat.min_price) if stat.min_price else None,
            "median": float(stat.median_price) if stat.median_price else None,
            "max": float(stat.max_price) if stat.max_price else None,
            "listing_count": stat.listing_count,
        }
