"""
FastAPI dependencies for ServerDeals — DB session, scoring engine, etc.

Gracefully degrades when DATABASE_URL is not set or the DB is unreachable
— all routes return empty arrays / zero counts in that case.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Database session — may be unavailable ──────────────────────────────────

_DB_AVAILABLE = False
_AsyncSessionLocal = None

try:
    from backend.db.database import AsyncSessionLocal as _scoped  # type: ignore[assignment]

    _AsyncSessionLocal = _scoped
    _DB_AVAILABLE = True
except Exception:
    logger.warning(
        "DATABASE_URL is not set or database module failed to load — "
        "API will start but all DB-dependent endpoints will return empty results."
    )


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    Yield an async SQLAlchemy session, or ``None`` if the database is unavailable.

    When DB is available: commits on success, rolls back on exception.
    When DB is unavailable: yields ``None`` immediately (no-op).
    """
    if not _DB_AVAILABLE or _AsyncSessionLocal is None:
        yield None
        return

    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
