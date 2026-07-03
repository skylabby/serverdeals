"""ServerDeals scoring package — deal scoring engine and affiliate URL tools."""

from backend.scoring.engine import DealScoringEngine
from backend.scoring.affiliate import add_affiliate_tag

__all__ = ["DealScoringEngine", "add_affiliate_tag"]
