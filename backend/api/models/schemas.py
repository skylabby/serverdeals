"""
Pydantic schemas for the ServerDeals REST API.

All fields use from_attributes=True so they map seamlessly from
SQLAlchemy model instances via response_model.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Deal Schemas
# ─────────────────────────────────────────────────────────────────────────────


class DealOut(BaseModel):
    """Public deal representation returned by all deal endpoints."""

    id: int
    ebay_item_id: str
    title: str
    price: Optional[float] = None
    currency: str = "USD"
    condition: Optional[str] = None
    listing_type: Optional[str] = None
    image_url: Optional[str] = None
    category_key: str
    category_display: str = ""
    score: Optional[float] = None
    classification: Optional[str] = None
    price_range: Optional[str] = None
    view_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("price", mode="before")
    @classmethod
    def _decimal_to_float(cls, v: object) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return float(v)
        return float(v)  # type: ignore[arg-type]


class PricePoint(BaseModel):
    """Single price-history data point."""

    price: float
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("price", mode="before")
    @classmethod
    def _decimal_to_float(cls, v: object) -> float:
        if isinstance(v, Decimal):
            return float(v)
        return float(v)  # type: ignore[arg-type]


class DealDetailOut(DealOut):
    """Single deal with price history attached."""

    price_history: list[PricePoint] = []


# ─────────────────────────────────────────────────────────────────────────────
# Category Schemas
# ─────────────────────────────────────────────────────────────────────────────


class CategoryOut(BaseModel):
    """Public category representation."""

    key: str
    display_name: str
    group_key: str
    listing_count: int = 0
    median_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("median_price", mode="before")
    @classmethod
    def _decimal_to_float(cls, v: object) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return float(v)
        return float(v)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────────────
# Stats Schema
# ─────────────────────────────────────────────────────────────────────────────


class StatsOut(BaseModel):
    """Live counters returned by GET /api/stats."""

    total_listings: int = 0
    total_categories: int = 0
    hot_deals_count: int = 0
    good_deals_count: int = 0
    last_updated: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    page: int
    total_pages: int
    total_items: int
