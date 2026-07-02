"""initial_schema

Revision ID: e39eab9cd2c9
Revises:
Create Date: 2026-07-02 19:49:23.854652

Creates the four core tables:
  - categories
  - listings
  - price_snapshots
  - model_stats
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e39eab9cd2c9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── categories ───────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("ebay_search_query", sa.String(256), nullable=False),
        sa.Column("group_key", sa.String(32), nullable=False),
        sa.Column("ebay_category_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("key", name=op.f("uq_categories_key")),
    )
    op.create_index(op.f("ix_categories_group_key"), "categories", ["group_key"])
    op.create_index(op.f("ix_categories_key"), "categories", ["key"])

    # ── listings ─────────────────────────────────────────────────────
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ebay_item_id", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("condition", sa.String(64), nullable=True),
        sa.Column("listing_type", sa.String(32), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("category_key", sa.String(64), nullable=False),
        sa.Column("specs_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "first_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_listings_category_key_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listings")),
        sa.UniqueConstraint("ebay_item_id", name=op.f("uq_listings_ebay_item_id")),
    )
    op.create_index(op.f("ix_listings_category_key"), "listings", ["category_key"])
    op.create_index(op.f("ix_listings_ebay_item_id"), "listings", ["ebay_item_id"])
    op.create_index("ix_listings_category_price", "listings", ["category_key", "price"])
    op.create_index("ix_listings_first_seen", "listings", ["first_seen"])

    # ── price_snapshots ──────────────────────────────────────────────
    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_price_snapshots_listing_id_listings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_snapshots")),
    )
    op.create_index(
        op.f("ix_price_snapshots_listing_id"), "price_snapshots", ["listing_id"]
    )
    op.create_index(
        "ix_snapshots_listing_captured",
        "price_snapshots",
        ["listing_id", "captured_at"],
    )

    # ── model_stats ─────────────────────────────────────────────────
    op.create_table(
        "model_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_key", sa.String(64), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("median_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("min_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("max_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("listing_count", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_model_stats_category_key_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_stats")),
        sa.UniqueConstraint(
            "category_key", "date", name="uq_model_stats_category_date"
        ),
    )
    op.create_index(
        op.f("ix_model_stats_category_key"), "model_stats", ["category_key"]
    )
    op.create_index("ix_model_stats_date", "model_stats", ["date"])


def downgrade() -> None:
    op.drop_table("model_stats")
    op.drop_table("price_snapshots")
    op.drop_table("listings")
    op.drop_table("categories")
