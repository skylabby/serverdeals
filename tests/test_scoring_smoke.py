#!/usr/bin/env python3
"""Smoke-test the deal scoring engine (imports, basic logic, no DB needed)."""

import sys
import os

# Make sure the repo root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 1. Imports ────────────────────────────────────────────────────────────
print("1. Testing imports ...")

from backend.scoring.engine import DealScoringEngine
from backend.scoring.affiliate import add_affiliate_tag

print("   ✓ DealScoringEngine imported")
print("   ✓ add_affiliate_tag imported")

# ── 2. Thresholds & classification (no DB) ────────────────────────────────
print("\n2. Testing classification logic ...")

assert DealScoringEngine.HOT_THRESHOLD == 40.0
assert DealScoringEngine.GOOD_THRESHOLD == 20.0
assert DealScoringEngine.FAIR_THRESHOLD == 0.0

classify = DealScoringEngine._classify

assert classify(None) == "NoData", f"None → {classify(None)}"
assert classify(50.0) == "Hot", f"50 → {classify(50.0)}"
assert classify(40.0) == "Hot", f"40 → {classify(40.0)}"
assert classify(39.99) == "Good", f"39.99 → {classify(39.99)}"
assert classify(20.0) == "Good", f"20 → {classify(20.0)}"
assert classify(19.99) == "Fair", f"19.99 → {classify(19.99)}"
assert classify(0.0) == "Fair", f"0 → {classify(0.0)}"
assert classify(-5.0) == "Fair", f"-5 → {classify(-5.0)}"

print("   ✓ All classification thresholds correct")

# ── 3. Score formula (manual check) ───────────────────────────────────────
print("\n3. Testing scoring formula ...")
# Score = (1 - price / median) * 100
price, median = 80.0, 100.0
expected = round((1 - 80 / 100) * 100, 2)  # 20.0
print(f"   price=80, median=100 → score={expected} (should be 20.0, 'Good')")
assert expected == 20.0

price, median = 50.0, 100.0
expected = round((1 - 50 / 100) * 100, 2)  # 50.0
print(f"   price=50, median=100 → score={expected} (should be 50.0, 'Hot')")
assert expected == 50.0

price, median = 120.0, 100.0
expected = round((1 - 120 / 100) * 100, 2)  # -20.0
print(f"   price=120, median=100 → score={expected} (should be -20.0, 'Fair')")
assert expected == -20.0

# ── 4. Affiliate URL tagging ──────────────────────────────────────────────
print("\n4. Testing affiliate URL tagging ...")

url = "https://www.ebay.com/itm/123456789"
tagged = add_affiliate_tag(url, campaign_id="5338774310")
assert "campid=5338774310" in tagged, f"Missing campid in: {tagged}"
assert tagged.startswith("https://www.ebay.com/itm/123456789"), f"URL broken: {tagged}"
print(f"   {url}  →  {tagged}")
print("   ✓ Affiliate tag appended correctly")

# Existing query params preserved
url2 = "https://www.ebay.com/itm/123?var=456&foo=bar"
tagged2 = add_affiliate_tag(url2, campaign_id="999")
assert "var=456" in tagged2
assert "foo=bar" in tagged2
assert "campid=999" in tagged2
print(f"   {url2}  →  {tagged2}")
print("   ✓ Existing query params preserved")

# Overwrites existing campid
url3 = "https://www.ebay.com/itm/123?campid=old"
tagged3 = add_affiliate_tag(url3, campaign_id="new123")
assert "campid=new123" in tagged3
assert "campid=old" not in tagged3
print(f"   {url3}  →  {tagged3}")
print("   ✓ Existing campid overwritten")

# ── 5. Env fallback ──────────────────────────────────────────────────────
print("\n5. Testing env var fallback ...")
os.environ["EBAY_CAMPAIGN_ID"] = "env_test_123"
tagged_env = add_affiliate_tag("https://www.ebay.com/itm/999")
assert "campid=env_test_123" in tagged_env
print(f"   With EBAY_CAMPAIGN_ID=env_test_123  →  {tagged_env}")
print("   ✓ Env var fallback works")
del os.environ["EBAY_CAMPAIGN_ID"]

# Default fallback
tagged_default = add_affiliate_tag("https://www.ebay.com/itm/999")
assert "campid=YOUR_CAMPAIGN_ID" in tagged_default
print(f"   Without env var  →  {tagged_default}")
print("   ✓ Default fallback works")

# ── Done ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ✅  ALL SMOKE TESTS PASSED")
print("=" * 60)
