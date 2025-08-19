"""Legal rationale utilities."""
from __future__ import annotations

from typing import Any, Dict

from app.models import CandidateSchedule
from app.rules.engine import load_rule_pack

RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULE_MAP: Dict[str, Dict[str, Any]] | None = None


def _rules() -> Dict[str, Dict[str, Any]]:
    global _RULE_MAP
    if _RULE_MAP is None:
        data = load_rule_pack(RULE_PACK_PATH)
        mapping: Dict[str, Dict[str, Any]] = {}
        for bucket in ("hard", "soft"):
            for rule in data.get(bucket, []):
                mapping[rule.get("id")] = rule
        _RULE_MAP = mapping
    return _RULE_MAP


def explain(candidate: CandidateSchedule, report: dict[str, Any]) -> list[str]:
    """Return legal explanations for a candidate schedule.

    Parameters
    ----------
    candidate:
        The schedule to annotate.
    report:
        Validation output containing ``violations`` entries with ``pairing_id``
        and ``rule`` keys.
    """

    messages: list[str] = []
    mapping = _rules()
    violations = report.get("violations", [])
    for v in violations:
        if v.get("pairing_id") in candidate.pairings:
            rid = v.get("rule")
            meta = mapping.get(rid, {})
            desc = meta.get("desc", rid)
            clause = meta.get("clause")
            if clause:
                messages.append(f"{rid}: {desc} ({clause})")
            else:
                messages.append(f"{rid}: {desc}")
    return messages
