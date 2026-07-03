"""
Shared configuration for the eBay scraper.

Reads credentials from environment / .env via python-dotenv.
Centralizes all tunables: API endpoints, rate limits, retry settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (two levels up from backend/scraper/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")


# ── eBay API Credentials ────────────────────────────────────────────────

EBAY_APP_ID: str = os.getenv("EBAY_APP_ID", "")
EBAY_DEV_ID: str = os.getenv("EBAY_DEV_ID", "")
EBAY_CERT_ID: str = os.getenv("EBAY_CERT_ID", "")
EBAY_ENV: str = os.getenv("EBAY_ENV", "sandbox")


# ── eBay API Endpoints (Buy Browse API — REST/JSON with OAuth) ──────────

EBAY_OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BUY_BROWSE_BASE = "https://api.ebay.com/buy/browse/v1"
EBAY_OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"


# ── Rate Limiting ───────────────────────────────────────────────────────

# Sandbox: 5000 calls/day → ~3.5 calls/min sustained; we batch in bursts
# Production: varies by tier; 5000/day default for compatible apps
DAILY_CALL_LIMIT = int(os.getenv("EBAY_DAILY_CALL_LIMIT", "5000"))

# Minimum seconds between successive API calls (safety margin)
MIN_CALL_INTERVAL_SEC = float(os.getenv("EBAY_MIN_CALL_INTERVAL", "0.5"))

# Max concurrent API calls (we don't go above 1 to respect rate limits)
MAX_CONCURRENT_CALLS = int(os.getenv("EBAY_MAX_CONCURRENT", "1"))


# ── Request Settings ────────────────────────────────────────────────────

# Max items per page (eBay Finding API: max 100)
PAGE_SIZE = int(os.getenv("EBAY_PAGE_SIZE", "100"))

# Max pages to fetch per category per run (0 = unlimited)
MAX_PAGES_PER_CATEGORY = int(os.getenv("EBAY_MAX_PAGES_PER_CATEGORY", "3"))

# HTTP request timeout in seconds
REQUEST_TIMEOUT = float(os.getenv("EBAY_REQUEST_TIMEOUT", "30"))


# ── Retry / Backoff ─────────────────────────────────────────────────────

# Max retry attempts on transient failures (5xx, timeout, connection)
MAX_RETRIES = int(os.getenv("EBAY_MAX_RETRIES", "3"))

# Base backoff seconds (doubles each retry: 1, 2, 4, ...)
RETRY_BACKOFF_BASE = float(os.getenv("EBAY_RETRY_BACKOFF_BASE", "1.0"))

# HTTP status codes treated as retryable
RETRYABLE_STATUS_CODES: tuple[int, ...] = (429, 500, 502, 503, 504)


# ── Scheduler ───────────────────────────────────────────────────────────

# Cron schedule string (every 3 hours by default)
SCRAPE_CRON_SCHEDULE = os.getenv("SCRAPE_CRON_SCHEDULE", "0 */3 * * *")

# Whether to run a scrape immediately on scheduler start
SCRAPE_ON_STARTUP = os.getenv("SCRAPE_ON_STARTUP", "true").lower() in ("1", "true", "yes")


# ── Logging ─────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
