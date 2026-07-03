"""
Async Telegram alert system for ServerDeals.

Sends formatted deal alerts via the Telegram Bot API using httpx.
Includes built-in rate limiting (max 10 messages per minute).

Environment variables:
    TELEGRAM_BOT_TOKEN  — Telegram bot token from @BotFather
    TELEGRAM_CHAT_ID    — Default chat ID (optional; can be overridden)

Usage:
    from backend.alerts.telegram import send_deal_alert

    success = await send_deal_alert(chat_id=123456789, deals=deals)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import deque
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = "https://api.telegram.org"

# ── Rate Limiter ─────────────────────────────────────────────────────────────
# Allows at most MAX_MESSAGES per WINDOW_SECONDS, queuing excess sends.

_MAX_MESSAGES = 10
_WINDOW_SECONDS = 60.0
_send_timestamps: deque[float] = deque()
_rate_lock = asyncio.Lock()


async def _acquire_rate_limit_slot() -> None:
    """Wait until a send slot is available under the rate limit."""
    async with _rate_lock:
        now = time.monotonic()
        # Purge timestamps older than the window
        while _send_timestamps and _send_timestamps[0] <= now - _WINDOW_SECONDS:
            _send_timestamps.popleft()

        if len(_send_timestamps) >= _MAX_MESSAGES:
            wait = _send_timestamps[0] + _WINDOW_SECONDS - now
            if wait > 0:
                logger.debug("Telegram rate limit — waiting %.1fs", wait)
                await asyncio.sleep(wait)
                # Re-check after sleep
                await _acquire_rate_limit_slot()
                return

        _send_timestamps.append(time.monotonic())


# ── Formatter ────────────────────────────────────────────────────────────────


def _format_deal_message(deals: list[dict[str, Any]]) -> str:
    """Format a list of deals into a Telegram MarkdownV2 message.

    Uses Telegram's MarkdownV2 for bold titles and clickable links.
    """
    if not deals:
        return "📭 *No deals found*"

    parts: list[str] = [f"🔥 *Top {len(deals)} Server Deals* 🔥\n"]

    for deal in deals:
        title = _escape_md(str(deal.get("title", "No title")))
        price = deal.get("price")
        currency = deal.get("currency", "USD")
        score = deal.get("score")
        classification = str(deal.get("classification", "Fair")).upper()
        view_url = deal.get("view_url", "")

        price_str = f"${float(price):,.2f}" if price else "N/A"
        score_str = f"{score}%" if score is not None else "—"

        line = (
            f"• *{title}*\n"
            f"  💰 {price_str} {currency} · {classification} · 📊 {score_str}"
        )
        if view_url:
            line += f"\n  [View on eBay]({view_url})"

        parts.append(line)

    return "\n".join(parts)


def _escape_md(text: str) -> str:
    """Escape special MarkdownV2 characters for Telegram."""
    special = "_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


# ── Public API ───────────────────────────────────────────────────────────────


async def send_deal_alert(
    chat_id: str | int | None = None,
    deals: list[dict[str, Any]] | None = None,
    *,
    message: str | None = None,
) -> bool:
    """Send a deal alert to a Telegram chat.

    Parameters
    ----------
    chat_id : str | int, optional
        Target Telegram chat ID. Falls back to TELEGRAM_CHAT_ID env var.
    deals : list[dict], optional
        Each dict should have: title, price, currency, score,
        classification, view_url. If provided, a formatted deal summary
        is built automatically.
    message : str, optional
        Custom MarkdownV2 message. Overrides the auto-generated deal
        format. Useful for sending arbitrary alerts.

    Returns
    -------
    bool
        True if the message was sent successfully, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — cannot send Telegram alert.")
        return False

    target_chat = chat_id or TELEGRAM_CHAT_ID
    if not target_chat:
        logger.warning("No Telegram chat_id provided and TELEGRAM_CHAT_ID not set.")
        return False

    text = message if message else _format_deal_message(deals or [])

    url = f"{TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload: dict[str, Any] = {
        "chat_id": str(target_chat),
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }

    await _acquire_rate_limit_slot()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("ok"):
                logger.error(
                    "Telegram API error: %s (code=%s)",
                    data.get("description", "unknown"),
                    data.get("error_code", "—"),
                )
                return False

        logger.info(
            "Telegram alert sent to %s — %d deals",
            target_chat,
            len(deals) if deals else 0,
        )
        return True

    except httpx.HTTPStatusError as exc:
        logger.error("Telegram HTTP error: %s — %s", exc.response.status_code, exc.response.text)
        return False
    except httpx.RequestError as exc:
        logger.error("Telegram request failed: %s", exc)
        return False
    except Exception:
        logger.exception("Unexpected error sending Telegram alert")
        return False


async def send_message(chat_id: str | int, text: str) -> bool:
    """Send a plain MarkdownV2 message to a Telegram chat.

    Convenience wrapper around send_deal_alert for non-deal messages.
    """
    return await send_deal_alert(chat_id=chat_id, message=text)
