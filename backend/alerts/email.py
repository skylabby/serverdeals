"""
Async email alert system for ServerDeals.

Sends HTML-formatted deal alert emails via SMTP using aiosmtplib.
Configuration is read from environment variables.

Environment variables:
    SMTP_HOST  — SMTP server hostname (e.g. smtp.gmail.com)
    SMTP_PORT  — SMTP server port (default 587)
    SMTP_USER  — SMTP authentication username
    SMTP_PASS  — SMTP authentication password
    EMAIL_FROM — Sender address (defaults to SMTP_USER)

Usage:
    from backend.alerts.email import send_deal_alert

    await send_deal_alert("user@example.com", deals)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER) or SMTP_USER

# ── HTML Template ────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
        .container {{ max-width: 640px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                   padding: 24px; border-radius: 12px 12px 0 0; }}
        .header h1 {{ margin: 0; color: #fff; font-size: 22px; }}
        .header p {{ margin: 6px 0 0; color: #bfdbfe; font-size: 14px; }}
        .deal {{ display: flex; gap: 16px; padding: 16px; border-bottom: 1px solid #1e293b;
                 background: #1e293b; margin: 1px 0; border-radius: 4px; }}
        .deal:last-child {{ border-bottom: none; }}
        .deal img {{ width: 120px; height: 90px; object-fit: contain; border-radius: 6px;
                      background: #0f172a; flex-shrink: 0; }}
        .deal-info {{ flex: 1; min-width: 0; }}
        .deal-title {{ font-size: 14px; font-weight: 600; margin: 0 0 4px;
                       white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .price {{ font-size: 20px; font-weight: 700; color: #34d399; }}
        .score {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
                  font-size: 12px; font-weight: 700; }}
        .score-hot {{ background: #dc2626; color: #fff; }}
        .score-good {{ background: #f59e0b; color: #0f172a; }}
        .score-fair {{ background: #64748b; color: #e2e8f0; }}
        .view-link {{ font-size: 12px; color: #60a5fa; text-decoration: none; }}
        .view-link:hover {{ text-decoration: underline; }}
        .footer {{ text-align: center; padding: 16px; color: #64748b; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 ServerDeals — Top Deals Alert</h1>
            <p>{deal_count} hot deals found on eBay US · {date}</p>
        </div>
        {deals_html}
        <div class="footer">
            <p>ServerDeals · Automated deal alerts · <a href="{site_url}" style="color:#60a5fa;">View All Deals</a></p>
        </div>
    </div>
</body>
</html>
"""

_DEAL_ROW_TEMPLATE = """\
<div class="deal">
    {image_html}
    <div class="deal-info">
        <h3 class="deal-title">{title}</h3>
        <span class="price">{currency} ${price:,.2f}</span>
        <span class="score {score_class}">{classification} · {score}%</span>
        &nbsp;
        <a class="view-link" href="{view_url}">View on eBay →</a>
    </div>
</div>
"""


def _render_html(deals: list[dict[str, Any]], site_url: str = "") -> str:
    """Render the full HTML email from a list of deal dicts."""
    from datetime import date

    rows: list[str] = []
    for deal in deals:
        classification = str(deal.get("classification", "Fair")).lower()
        score_class = {
            "hot": "score-hot",
            "good": "score-good",
            "fair": "score-fair",
            "nodata": "score-fair",
        }.get(classification, "score-fair")

        image_url = deal.get("image_url")
        image_html = (
            f'<img src="{image_url}" alt="" />'
            if image_url
            else '<img src="" alt="No image" style="opacity:0.3;" />'
        )

        rows.append(
            _DEAL_ROW_TEMPLATE.format(
                image_html=image_html,
                title=deal.get("title", "No title"),
                currency=deal.get("currency", "USD"),
                price=float(deal.get("price", 0) or 0),
                score_class=score_class,
                classification=classification.upper(),
                score=deal.get("score") or "—",
                view_url=deal.get("view_url", "#"),
            )
        )

    return _HTML_TEMPLATE.format(
        deal_count=len(deals),
        date=date.today().isoformat(),
        deals_html="\n".join(rows) if rows else "<p style='padding:16px'>No deals to show.</p>",
        site_url=site_url or "#",
    )


# ── Public API ───────────────────────────────────────────────────────────────


async def send_deal_alert(
    email: str,
    deals: list[dict[str, Any]],
    *,
    subject: str | None = None,
    site_url: str = "",
) -> bool:
    """Send an HTML deal alert email.

    Parameters
    ----------
    email : str
        Recipient email address.
    deals : list[dict]
        Each dict should have keys: title, price, currency, score,
        classification, image_url, view_url.
    subject : str, optional
        Custom subject line. Defaults to "🔥 Top Server Deals — {date}".
    site_url : str, optional
        Base URL of the ServerDeals site for the footer link.

    Returns
    -------
    bool
        True if the email was sent successfully, False otherwise.
    """
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        logger.warning(
            "SMTP not configured (SMTP_HOST=%s, SMTP_USER=%s). Skipping email alert.",
            SMTP_HOST or "<unset>",
            SMTP_USER or "<unset>",
        )
        return False

    from datetime import date

    subject = subject or f"🔥 Top Server Deals — {date.today().isoformat()}"
    html_body = _render_html(deals, site_url=site_url)

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_FROM
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        smtp = aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT, use_tls=False)
        await smtp.connect()
        await smtp.starttls()
        await smtp.login(SMTP_USER, SMTP_PASS)
        await smtp.send_message(msg)
        await smtp.quit()

        logger.info("Email alert sent to %s — %d deals", email, len(deals))
        return True
    except aiosmtplib.SMTPException as exc:
        logger.error("SMTP error sending alert to %s: %s", email, exc)
        return False
    except Exception as exc:
        logger.exception("Unexpected error sending email alert to %s", email)
        return False
