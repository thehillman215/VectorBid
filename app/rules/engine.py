from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models import FeatureBundle


def load_rule_pack(path: str) -> dict[str, Any]:
    """Load a YAML rule pack, resolving relative paths robustly."""
    pth = Path(path)
    candidates = []
    if pth.is_absolute():
        candidates.append(pth)
    else:
        repo_root = Path(__file__).resolve().parents[2]
        candidates.extend([repo_root / path, Path.cwd() / path])
    for c in candidates:
        c = c.resolve()
        if c.exists():
            with open(c) as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(f"Rule pack not found in any candidate: {[str(c) for c in candidates]}")

def _eval_hard(pref: dict[str, Any], pairing: dict[str, Any], rule: dict[str, Any]) -> bool:
    rid = rule.get("id")
    if rid == "FAR117_MIN_REST":
        return (pairing.get("rest_hours", 999) >= 10)
    if rid == "NO_REDEYE_IF_SET":
        if pref.get("hard_constraints", {}).get("no_red_eyes"):
            return pairing.get("redeye") is False
        return True
    return True  # unknown hard rule → allow (fail-open for now)

def validate_feasibility(bundle: FeatureBundle, rules: dict[str, Any]) -> dict[str, Any]:
    pref = bundle.preference_schema.model_dump()
    pairings = bundle.pairing_features.get("pairings", [])
    violations: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    for p in pairings:
        ok = True
        for r in rules.get("hard", []):
            if not _eval_hard(pref, p, r):
                ok = False
                violations.append({"pairing_id": p.get("id"), "rule": r.get("id")})
        if ok:
            feasible.append(p)
    return {"violations": violations, "feasible_pairings": feasible}
