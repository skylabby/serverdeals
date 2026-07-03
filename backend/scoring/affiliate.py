"""
eBay affiliate URL transformation.

Appends the EPN (eBay Partner Network) campaign ID to eBay item URLs
so that clicks earn affiliate revenue.

Environment variable:
    EBAY_CAMPAIGN_ID  —  your EPN campaign ID (e.g. "533xxxxxxxx")
    If unset, the placeholder ``"YOUR_CAMPAIGN_ID"`` is used.

Usage:
    >>> from backend.scoring.affiliate import add_affiliate_tag
    >>> add_affiliate_tag("https://www.ebay.com/itm/123456789")
    'https://www.ebay.com/itm/123456789?campid=5338774310'
"""

from __future__ import annotations

import os
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def _get_campaign_id() -> str:
    return os.getenv("EBAY_CAMPAIGN_ID", "YOUR_CAMPAIGN_ID")


def add_affiliate_tag(url: str, campaign_id: str | None = None) -> str:
    """Append (or replace) the ``campid`` query parameter on an eBay URL.

    Parameters
    ----------
    url : str
        An eBay listing URL (e.g. ``https://www.ebay.com/itm/123456``).
    campaign_id : str, optional
        Override the campaign ID.  When ``None`` the value of the
        ``EBAY_CAMPAIGN_ID`` environment variable is used.

    Returns
    -------
    str
        The URL with ``?campid=...`` appended (or updated).
    """
    cid = campaign_id or _get_campaign_id()
    parsed = urlparse(url)

    # parse_qs returns {k: [v1, v2]} — flatten to single values
    query_pairs: list[tuple[str, str]] = []
    for k, vals in parse_qs(parsed.query, keep_blank_values=True).items():
        if k != "campid":
            query_pairs.append((k, vals[0]))

    query_pairs.append(("campid", cid))

    return urlunparse(parsed._replace(query=urlencode(query_pairs)))
