#!/usr/bin/env python3
"""
Seed the `categories` table with the 25 ServerDeals hardware categories.

Usage:
    python -m backend.db.seed       # from repo root
    python backend/db/seed.py       # if PYTHONPATH includes parent
"""

import asyncio
import sys

# Ensure the repo-root is on sys.path so imports work from any cwd
try:
    from backend.db.database import AsyncSessionLocal
    from backend.db.models import Category
    from backend.scraper.categories import CATEGORIES
except ModuleNotFoundError:
    # Running as `python backend/db/seed.py` from repo root
    sys.path.insert(0, ".")
    from backend.db.database import AsyncSessionLocal
    from backend.db.models import Category
    from backend.scraper.categories import CATEGORIES


async def seed_categories() -> None:
    """Insert or update all 25 category definitions."""
    async with AsyncSessionLocal() as session:
        for cd in CATEGORIES:
            existing = await session.get(Category, cd.key)
            if existing is not None:
                # Update in case search query or group changed
                existing.display_name = cd.display_name
                existing.ebay_search_query = cd.ebay_search_query
                existing.group_key = cd.group_key
                existing.ebay_category_id = cd.ebay_category_id
                print(f"  [updated] {cd.key}")
            else:
                session.add(
                    Category(
                        key=cd.key,
                        display_name=cd.display_name,
                        ebay_search_query=cd.ebay_search_query,
                        group_key=cd.group_key,
                        ebay_category_id=cd.ebay_category_id,
                    )
                )
                print(f"  [created] {cd.key}")

        await session.commit()

    print(f"\nDone — {len(CATEGORIES)} categories seeded.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
