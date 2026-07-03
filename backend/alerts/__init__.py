"""
ServerDeals alert system — email and Telegram notifications.

Exports:
    send_deal_alert(email, deals)   — Send HTML deal alert via SMTP
    send_telegram_alert(chat_id, deals) — Send deal alert via Telegram Bot API
    send_telegram_message(chat_id, text) — Send arbitrary message via Telegram
"""

from backend.alerts.email import send_deal_alert
from backend.alerts.telegram import send_deal_alert as send_telegram_alert
from backend.alerts.telegram import send_message as send_telegram_message

__all__ = [
    "send_deal_alert",
    "send_telegram_alert",
    "send_telegram_message",
]
