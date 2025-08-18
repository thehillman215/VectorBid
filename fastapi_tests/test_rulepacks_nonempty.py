"""
Test that rule packs have non-empty hard and soft buckets after merging.

This is a CI tripwire to ensure rule packs are properly structured.
"""

import sys
from pathlib import Path

# Ensure app is importable
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.rules.engine import load_rule_pack


def test_ual_2025_08_rule_pack_nonempty():
    """Test that UAL 2025.08 rule pack has non-empty merged buckets."""
    rule_pack_path = "rule_packs/UAL/2025.08.yml"

    # Load the rule pack
    rp = load_rule_pack(rule_pack_path, force_reload=True)

    # Verify merged buckets are non-empty
    assert rp["hard"], f"Merged hard rules bucket is empty in {rule_pack_path}"
    assert rp["soft"], f"Merged soft rules bucket is empty in {rule_pack_path}"

    # The rule pack loader merges far117 and union sections into hard/soft buckets
    # So we just verify the merged buckets exist and have content


def test_current_month_packs_nonempty():
    """Test that current month rule packs have non-empty buckets."""
    from datetime import datetime

    # Get current month in YYYY.MM format
    current_month = datetime.now().strftime("%Y.%m")

    # Look for rule packs for current month
    rule_pack_dir = Path("rule_packs")
    if rule_pack_dir.exists():
        for airline_dir in rule_pack_dir.iterdir():
            if airline_dir.is_dir():
                current_pack = airline_dir / f"{current_month}.yml"
                if current_pack.exists():
                    rp = load_rule_pack(str(current_pack), force_reload=True)
                    assert rp["hard"], f"Empty hard rules in {current_pack}"
                    assert rp["soft"], f"Empty soft rules in {current_pack}"
