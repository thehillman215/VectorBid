"""
Guard test to prevent rule pack regressions.
Ensures load_rule_pack() returns non-empty hard/soft buckets.
"""

import pytest


def test_ual_2025_08_rule_pack_non_empty():
    """Test that UAL 2025.08 rule pack has non-empty hard and soft buckets."""
    try:
        from app.rules.engine import load_rule_pack
    except ImportError:
        pytest.skip("app.rules.engine not available")

    # Load the rule pack with merge enabled
    rule_pack_path = "rule_packs/UAL/2025.08.yml"
    try:
        rp = load_rule_pack(rule_pack_path, True)
    except Exception as e:
        pytest.fail(f"Failed to load rule pack {rule_pack_path}: {e}")

    # Assert both hard and soft buckets are non-empty
    assert rp.get("hard"), f"Hard rules bucket is empty in {rule_pack_path}"
    assert rp.get("soft"), f"Soft rules bucket is empty in {rule_pack_path}"

    # Additional validation
    assert len(rp["hard"]) > 0, "Hard rules list should contain rules"
    assert len(rp["soft"]) > 0, "Soft rules list should contain rules"

    print(
        f"✅ Rule pack validation passed: {len(rp['hard'])} hard, {len(rp['soft'])} soft rules"
    )


def test_rule_pack_structure_validity():
    """Test that the rule pack has the expected structure."""
    import os

    import yaml

    rule_pack_path = "rule_packs/UAL/2025.08.yml"

    if not os.path.exists(rule_pack_path):
        pytest.skip(f"Rule pack file {rule_pack_path} not found")

    with open(rule_pack_path) as f:
        data = yaml.safe_load(f)

    # Check required top-level keys
    required_keys = ["version", "airline", "far117", "union", "id"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"

    # Check far117 and union sections have hard/soft
    for section in ["far117", "union"]:
        assert "hard" in data[section], f"Missing 'hard' in {section}"
        assert "soft" in data[section], f"Missing 'soft' in {section}"
        assert isinstance(data[section]["hard"], list), (
            f"{section}.hard should be a list"
        )
        assert isinstance(data[section]["soft"], list), (
            f"{section}.soft should be a list"
        )

    print("✅ Rule pack structure validation passed")
