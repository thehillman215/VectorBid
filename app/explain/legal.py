"""Legal rationale utilities."""

from __future__ import annotations

from typing import Any, Optional

from app.models import CandidateSchedule
from app.rules.engine import load_rule_pack

RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULE_MAP: Optional[dict[str, dict[str, Any]]] = None


def _rules() -> dict[str, dict[str, Any]]:
    global _RULE_MAP
    if _RULE_MAP is None:
        data = load_rule_pack(RULE_PACK_PATH)
        mapping: dict[str, dict[str, Any]] = {}

        # Handle nested rule structure (far117, union, etc.)
        for _section_name, section_data in data.items():
            if isinstance(section_data, dict):
                for bucket in ("hard", "soft"):
                    rules_list = section_data.get(bucket, [])
                    if isinstance(rules_list, list):
                        for rule in rules_list:
                            if isinstance(rule, dict) and "id" in rule:
                                mapping[rule.get("id")] = rule

        # Also handle top-level hard/soft rules for backward compatibility
        for bucket in ("hard", "soft"):
            for rule in data.get(bucket, []):
                if isinstance(rule, dict) and "id" in rule:
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
