"""
FastAPI application entrypoint for ServerDeals.

Starts up, creates DB tables (if they don't exist), registers all
routers under /api, and enables CORS for development.

All DB-dependent operations degrade gracefully when DATABASE_URL
is not set or the database is unreachable.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import categories, deals, stats

logger = logging.getLogger(__name__)

# ── eBay Marketplace Deletion Notification ────────────────────────────────
# eBay requires a compliant HTTPS endpoint to enable production keysets.
# This responds to the challenge_code verification during setup and logs
# any actual deletion notifications for compliance.

EBAY_NOTIFICATION_TOKEN = "4d2caa7d1e03b2614f911b6b194f21f4999137d4e4a0f8ce"

# ── Database — may be unavailable ───────────────────────────────────────────

_engine = None
_Base = None

try:
    from backend.db.database import engine as _db_engine
    from backend.db.models import Base as _db_Base

    _engine = _db_engine
    _Base = _db_Base
except Exception:
    logger.warning(
        "Database module failed to load — API will start without DB connectivity."
    )


# ── Lifespan ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup, clean up on shutdown."""
    if _engine is not None and _Base is not None:
        logger.info("Starting ServerDeals API — creating DB tables if needed …")
        try:
            async with _engine.begin() as conn:
                await conn.run_sync(_Base.metadata.create_all)
            logger.info("DB tables ensured.")
        except Exception:
            logger.exception(
                "Could not connect to DB — tables not created. Running in degraded mode."
            )
    else:
        logger.info("Starting ServerDeals API in degraded mode (no database).")

    yield

    if _engine is not None:
        logger.info("Shutting down ServerDeals API — disposing engine.")
        await _engine.dispose()


# ── App Factory ─────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="ServerDeals API",
        description="REST API for browsing and scoring server hardware deals from eBay.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — wide open for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check (always works, even in degraded mode)
    @app.get("/api/health")
    async def health_check():
        db_ok = _engine is not None
        return {
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "unavailable",
        }

    # eBay Marketplace Account Deletion notification endpoint
    # eBay verifies with challenge_code GET, sends deletion XML POSTs later
    from fastapi import Request, Response

    @app.api_route("/ebay-notification", methods=["GET", "POST"])
    async def ebay_notification(request: Request):
        challenge = request.query_params.get("challenge_code")
        if challenge:
            # Verification: return challenge_code with 200
            logger.info("eBay notification endpoint VERIFIED (challenge: %s)", challenge)
            return Response(
                content=challenge,
                media_type="text/plain",
                headers={"Content-Type": "text/plain"},
            )
        # Actual deletion notification — log and acknowledge
        body = await request.body()
        logger.info("eBay deletion notification received: %s", body[:500] if body else "(empty)")
        return {"ok": True}

    # Register routers
    app.include_router(deals.router)
    app.include_router(categories.router)
    app.include_router(stats.router)

    return app


app = create_app()
