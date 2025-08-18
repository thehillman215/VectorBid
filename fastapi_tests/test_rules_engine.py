import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.models import (  # noqa: E402
    ContextSnapshot,
    FeatureBundle,
    HardConstraints,
    PreferenceSchema,
)
from app.rules.engine import (  # noqa: E402
    DEFAULT_RULES,
    load_rule_pack,
    validate_feasibility,
)


def test_load_rule_pack_merge_success(tmp_path):
    data = {
        "version": "v",
        "airline": "UAL",
        "far117": {"hard": [{"id": "A"}], "soft": [{"id": "S1"}]},
        "union": {"hard": [{"id": "B"}], "soft": [{"id": "S2"}]},
    }
    f = tmp_path / "rules.yml"
    f.write_text(yaml.safe_dump(data))
    merged = load_rule_pack(str(f))
    assert [r["id"] for r in merged["hard"]] == ["A", "B"]
    assert [r["id"] for r in merged["soft"]] == ["S1", "S2"]


def test_load_rule_pack_missing_keys(tmp_path, caplog):
    data = {"version": "v", "airline": "UAL", "far117": {"hard": []}}
    f = tmp_path / "rules.yml"
    f.write_text(yaml.safe_dump(data))
    with caplog.at_level("ERROR"):
        merged = load_rule_pack(str(f))
    assert merged == DEFAULT_RULES
    assert "missing required keys" in caplog.text.lower()


def test_load_rule_pack_file_not_found(tmp_path, caplog):
    with caplog.at_level("ERROR"):
        merged = load_rule_pack(str(tmp_path / "missing.yml"))
    assert merged == DEFAULT_RULES
    assert "rule pack not found" in caplog.text.lower()


def _bundle(no_red: bool, pairings: list[dict]) -> FeatureBundle:
    pref = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="EWR",
        seat="FO",
        equip=["73G"],
        hard_constraints=HardConstraints(no_red_eyes=no_red),
    )
    ctx = ContextSnapshot(
        ctx_id="ctx",
        pilot_id="p1",
        airline="UAL",
        base="EWR",
        seat="FO",
        equip=["73G"],
        seniority_percentile=0.5,
    )
    return FeatureBundle(
        context=ctx,
        preference_schema=pref,
        analytics_features={},
        compliance_flags={},
        pairing_features={"pairings": pairings},
    )


def test_far117_min_rest_check():
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml", True)
    bundle = _bundle(
        False,
        [
            {"id": "p1", "rest_hours": 9, "redeye": False},
            {"id": "p2", "rest_hours": 10, "redeye": False},
        ],
    )
    result = validate_feasibility(bundle, rules)
    assert {"pairing_id": "p1", "rule": "FAR117_MIN_REST"} in result["violations"]
    assert any(p["id"] == "p2" for p in result["feasible_pairings"])


def test_no_redeye_gating():
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml", True)
    bundle = _bundle(True, [{"id": "p1", "rest_hours": 12, "redeye": True}])
    result = validate_feasibility(bundle, rules)
    assert {"pairing_id": "p1", "rule": "NO_REDEYE_IF_SET"} in result["violations"]

    bundle_ok = _bundle(False, [{"id": "p1", "rest_hours": 12, "redeye": True}])
    result_ok = validate_feasibility(bundle_ok, rules)
    assert result_ok["violations"] == []
