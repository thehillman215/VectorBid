from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import defaultdict
from datetime import datetime, timedelta

import logging
import yaml

from app.models import FeatureBundle

logger = logging.getLogger(__name__)

DEFAULT_RULES: dict[str, list[Any]] = {"hard": [], "soft": []}


def load_rule_pack(path: str) -> dict[str, Any]:
    """Load and merge FAR117 and union rule packs from YAML.

    The YAML file must contain ``far117`` and ``union`` keys, each mapping to a
    dictionary with optional ``hard`` and ``soft`` lists. When any error occurs
    the function logs the issue and returns an empty default rule set.
    """

    pth = Path(path)
    if pth.is_absolute():
        candidates = [pth]
    else:
        repo_root = Path(__file__).resolve().parents[2]
        candidates = [repo_root / path, Path.cwd() / path]

    data: Any | None = None
    last_path: Path | None = None
    for c in candidates:
        last_path = c.resolve()
        try:
            with last_path.open() as f:
                data = yaml.safe_load(f)
            break
        except FileNotFoundError:
            continue
        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML rule file %s: %s", last_path, e)
            return DEFAULT_RULES.copy()

    if data is None:
        logger.error(
            "Rule pack not found in any candidate: %s",
            [str(c.resolve()) for c in candidates],
        )
        return DEFAULT_RULES.copy()

    if not isinstance(data, dict):
        logger.error("Unexpected structure in rule file %s", last_path)
        return DEFAULT_RULES.copy()

    missing = [k for k in ("far117", "union") if k not in data]
    if missing:
        logger.error("Rule file %s missing required keys: %s", last_path, ", ".join(missing))
        return DEFAULT_RULES.copy()

    far117 = data.get("far117") or {}
    union = data.get("union") or {}
    if not isinstance(far117, dict) or not isinstance(union, dict):
        logger.error("Rule file %s has invalid rule sections", last_path)
        return DEFAULT_RULES.copy()

    merged = {"hard": [], "soft": []}
    for section in ("hard", "soft"):
        f_section = far117.get(section, []) or []
        u_section = union.get(section, []) or []
        if not isinstance(f_section, list) or not isinstance(u_section, list):
            logger.error(
                "Rule file %s has invalid '%s' section structure", last_path, section
            )
            return DEFAULT_RULES.copy()
        merged[section].extend(f_section)
        merged[section].extend(u_section)

    return merged

def _eval_hard(pref: dict[str, Any], pairing: dict[str, Any], rule: dict[str, Any]) -> bool:
    rid = rule.get("id")
    if rid == "FAR117_MIN_REST":
        return (pairing.get("rest_hours", 999) >= 10)
    if rid == "NO_REDEYE_IF_SET":
        if pref.get("hard_constraints", {}).get("no_red_eyes"):
            return pairing.get("redeye") is False
        return True
    return True  # unknown hard rule → allow (fail-open for now)


def _week_start(date: datetime) -> datetime:
    """Return the first day of the week for ``date`` (Monday as day 0)."""
    return date - timedelta(days=date.weekday())

def validate_feasibility(bundle: FeatureBundle, rules: dict[str, Any]) -> dict[str, Any]:
    pref = bundle.preference_schema.model_dump()
    pairings = bundle.pairing_features.get("pairings", [])
    violations: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    weekly_block = defaultdict(float)
    for p in pairings:
        ok = True
        for r in rules.get("hard", []):
            if not _eval_hard(pref, p, r):
                ok = False
                violations.append({"pairing_id": p.get("id"), "rule": r.get("id")})
        if ok:
            feasible.append(p)

        report_date = (
            p.get("report_date")
            or p.get("report_time")
            or p.get("report")
        )
        if report_date:
            try:
                dt = datetime.fromisoformat(report_date)
                weekly_block[_week_start(dt)] += float(p.get("block_hours", 0))
            except ValueError:
                pass

    max_week = rules.get("far117", {}).get("max_block_hours_per_week")
    if max_week is not None:
        for week, total in weekly_block.items():
            if total > max_week:
                violations.append(
                    {
                        "rule": "FAR117_MAX_BLOCK_HOURS_PER_WEEK",
                        "week_start": week.date().isoformat(),
                        "block_hours": total,
                    }
                )

    return {"violations": violations, "feasible_pairings": feasible}
