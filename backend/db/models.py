"""
SQLAlchemy 2.0 async models for ServerDeals.

Tables:
  - listings        Scraped eBay listings (one row per discovered item)
  - price_snapshots  Price history for each listing (time series)
  - categories      25 hardware categories with eBay search mappings
  - model_stats      Daily aggregated stats per category (median/min/max price)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ebay_item_id: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="USD"
    )
    condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    listing_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # "auction", "fixed_price"
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_key: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("categories.key", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    specs_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="listings")
    snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        "PriceSnapshot", back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_listings_category_price", "category_key", "price"),
        Index("ix_listings_first_seen", "first_seen"),
    )

    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, ebay={self.ebay_item_id}, '{self.title[:40]}...')>"


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshots_listing_captured", "listing_id", "captured_at"),
    )

    def __repr__(self) -> str:
        return f"<PriceSnapshot(listing={self.listing_id}, ${self.price} @ {self.captured_at})>"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    ebay_search_query: Mapped[str] = mapped_column(String(256), nullable=False)
    group_key: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    ebay_category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(
        "Listing", back_populates="category"
    )
    stats: Mapped[list["ModelStats"]] = relationship(
        "ModelStats", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Category(key='{self.key}', '{self.display_name}')>"


class ModelStats(Base):
    __tablename__ = "model_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_key: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("categories.key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[datetime] = mapped_column(
        Date, nullable=False
    )  # date only — one row per category per day
    median_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    min_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    max_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    listing_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="stats")

    __table_args__ = (
        UniqueConstraint("category_key", "date", name="uq_model_stats_category_date"),
        Index("ix_model_stats_date", "date"),
    )

    def __repr__(self) -> str:
        return f"<ModelStats(cat='{self.category_key}', {self.date}, n={self.listing_count})>"
