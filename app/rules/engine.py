from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from app.models import FeatureBundle
from app.rules.models import HardRule, RulePack


<<<<<<< HEAD
def load_rule_pack(path: str) -> RulePack:
    """Load a YAML rule pack, resolving relative paths robustly."""
=======
# ---------------------------------------------------------------------------
# RulePack dataclass
# ---------------------------------------------------------------------------


@dataclass
class RulePack:
    """Container for airline rule configuration.

    The structure is intentionally lightweight – only the pieces required by the
    simplified validation engine are modelled.  ``far117`` contains parameters
    for FAA legality checks while ``union`` stores contract restrictions.
    """

    far117: Dict[str, Any] = field(default_factory=dict)
    union: Dict[str, Any] = field(default_factory=dict)

    # --- FAR 117 helpers -------------------------------------------------
    def get_max_duty_hours(self, start_time: str | time | datetime) -> float:
        """Return maximum duty period for a given report time."""

        if isinstance(start_time, str):
            start = datetime.strptime(start_time, "%H:%M").time()
        elif isinstance(start_time, datetime):
            start = start_time.time()
        else:
            start = start_time

        hour = start.hour + start.minute / 60.0
        for limit in self.far117.get("duty_limits", []):
            start_h = float(limit.get("start", 0))
            end_h = float(limit.get("end", 24))
            if start_h <= hour < end_h:
                return float(limit.get("max", 8))
        # default fallback
        return float(self.far117.get("default_duty_limit", 8))

    def get_min_rest(self, duty_hours: float) -> float:
        """Return minimum rest required following ``duty_hours`` duty."""

        if duty_hours is None:
            return float(self.far117.get("min_rest", 9))

        threshold = float(self.far117.get("extended_duty_threshold", 14))
        base_rest = float(self.far117.get("min_rest", 9))
        extended_rest = float(self.far117.get("extended_rest", 10))
        return extended_rest if duty_hours > threshold else base_rest


# ---------------------------------------------------------------------------
# Rule pack loading
# ---------------------------------------------------------------------------


def _default_rule_pack() -> RulePack:
    """Hard coded UAL defaults used when YAML files are missing."""

    default_cfg = {
        "far117": {
            "min_rest": 9,
            "extended_rest": 10,
            "extended_duty_threshold": 14,
            "duty_limits": [
                {"start": 5, "end": 12, "max": 9},
                {"start": 12, "end": 17, "max": 8.5},
                {"start": 0, "end": 5, "max": 8},
                {"start": 17, "end": 24, "max": 8},
            ],
            "max_block_hours_per_week": 32,
        },
        "union": {
            "min_days_off_per_month": 12,
            # "default" key acts as fallback for any base not explicitly listed.
            "max_block_hours_per_base": {"default": 100},
        },
    }
    return RulePack(**default_cfg)


def load_rule_pack(path: str) -> RulePack:
    """Load a YAML rule pack from ``path`` or return defaults if missing."""

>>>>>>> Add Flask dependencies and Replit DB fallback
    pth = Path(path)
    if not pth.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
<<<<<<< HEAD
        candidates.extend([repo_root / path, Path.cwd() / path])
    for c in candidates:
        c = c.resolve()
        if c.exists():
            with open(c) as f:
                data = yaml.safe_load(f)
            return RulePack.model_validate(data)
    raise FileNotFoundError(
        f"Rule pack not found in any candidate: {[str(c) for c in candidates]}"
    )

def _eval_hard(
    pref: dict[str, Any], pairing: dict[str, Any], rule: HardRule, pack: RulePack
) -> bool:
    rid = rule.id
    if rid == "FAR117_MIN_REST":
        return pairing.get("rest_hours", 999) >= pack.far117.min_rest_hours
    if rid == "NO_REDEYE_IF_SET":
        if pref.get("hard_constraints", {}).get("no_red_eyes"):
            return pairing.get("redeye") is False
        return True
    return True  # unknown hard rule → allow (fail-open for now)

def validate_feasibility(bundle: FeatureBundle, rules: RulePack) -> dict[str, Any]:
    pref = bundle.preference_schema.model_dump()
=======
        pth = repo_root / pth

    if pth.exists():
        with pth.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = _default_rule_pack()
        # merge loaded config
        cfg.far117.update(data.get("far117", {}))
        cfg.union.update(data.get("union", {}))
        return cfg
    # fall back to hard coded defaults
    return _default_rule_pack()


# ---------------------------------------------------------------------------
# Validation Engine
# ---------------------------------------------------------------------------


def _check_days_off(pair_days: Iterable[str], requested_off: Iterable[str]) -> str | None:
    for d in pair_days:
        if d in requested_off:
            return d
    return None


def validate_feasibility(bundle: FeatureBundle, rules: RulePack) -> Dict[str, Any]:
    """Validate a bundle of pairings against the provided ``RulePack``."""

    pref = bundle.preference_schema
    hard = pref.hard_constraints
>>>>>>> Add Flask dependencies and Replit DB fallback
    pairings = bundle.pairing_features.get("pairings", [])

    violations: List[Dict[str, Any]] = []
    feasible: List[Dict[str, Any]] = []

    requested_off = set(hard.days_off)

    for p in pairings:
        pid = p.get("id")
        ok = True
<<<<<<< HEAD
        for r in rules.hard:
            if not _eval_hard(pref, p, r, rules):
                ok = False
                violations.append({"pairing_id": p.get("id"), "rule": r.id})
        if ok:
            feasible.append(p)
    return {"violations": violations, "feasible_pairings": feasible}

# ============================================================
# Back-compat: merge sectioned YAML, safe fallbacks, minimal validator
# ============================================================
from pathlib import Path as _VB_Path
import logging as _VB_logging, os as _VB_os
from typing import Any as _VB_Any, Dict as _VB_Dict, List as _VB_List
try:
    import yaml as _VB_yaml  # type: ignore
except Exception:  # pragma: no cover
    _VB_yaml = None  # type: ignore

# cache
try:
    _RULE_CACHE  # type: ignore[name-defined]
except NameError:
    _RULE_CACHE: _VB_Dict[str, _VB_Dict[str, _VB_Any]] = {}

def _vb_merge_rule_dict(d: _VB_Dict[str, _VB_Any]) -> _VB_Dict[str, _VB_List[_VB_Dict[str, _VB_Any]]]:
    if not isinstance(d, dict):
        return {"hard": [], "soft": []}
    if "hard" in d or "soft" in d:
        return {"hard": list(d.get("hard", []) or []), "soft": list(d.get("soft", []) or [])}
    hard: _VB_List[_VB_Dict[str, _VB_Any]] = []
    soft: _VB_List[_VB_Dict[str, _VB_Any]] = []
    for sec in d.values():
        if isinstance(sec, dict):
            hard.extend(sec.get("hard", []) or [])
            soft.extend(sec.get("soft", []) or [])
    return {"hard": hard, "soft": soft}

def _vb_repo_root() -> _VB_Path:
    return _VB_Path(__file__).resolve().parents[2]

def _vb_default_rules_minimal() -> _VB_Dict[str, _VB_Any]:
    return {"hard": [{"id":"rest_min_10","desc":"Rest >= 10h","check":"pairing.rest_hours >= 10"}], "soft": []}

def _vb_load_default_rules_from_file() -> _VB_Dict[str, _VB_Any]:
    p = _VB_os.getenv("DEFAULT_RULE_PACK") or str(_vb_repo_root() / "rule_packs" / "UAL" / "2025.08.yml")
    try:
        if _VB_yaml is None:
            raise RuntimeError("pyyaml not available")
        with open(p, "r") as f:
            merged = _vb_merge_rule_dict(_VB_yaml.safe_load(f) or {})
        if not merged.get("hard"):
            raise ValueError("default rule pack missing 'hard'")
        return merged
    except Exception as e:  # pragma: no cover
        _VB_logging.error("Falling back to minimal DEFAULT_RULES: %s", e)
        return _vb_default_rules_minimal()

# Ensure DEFAULT_RULES exists & non-empty
try:
    DEFAULT_RULES  # type: ignore[name-defined]
except NameError:
    DEFAULT_RULES = _vb_load_default_rules_from_file()  # type: ignore[assignment]
else:
    if not isinstance(DEFAULT_RULES, dict) or not DEFAULT_RULES.get("hard"):
        DEFAULT_RULES = _vb_load_default_rules_from_file()  # type: ignore[assignment]

# Override/define load_rule_pack to always return unified dict and fallback to DEFAULT_RULES
def load_rule_pack(path: str, force_reload: bool = False):  # type: ignore[override]
    pth = _VB_Path(path)
    cands = [pth] if pth.is_absolute() else [_vb_repo_root() / path, _VB_Path.cwd() / path]
    for c in cands:
        c = c.resolve(); key = str(c)
        if not force_reload and key in _RULE_CACHE:
            return _RULE_CACHE[key]
        if c.exists():
            try:
                if _VB_yaml is None:
                    raise RuntimeError("pyyaml not available")
                merged = _vb_merge_rule_dict(_VB_yaml.safe_load(open(c)) or {})  # type: ignore[arg-type]
                if not merged.get("hard"):
                    _VB_logging.error("Rule pack missing required keys; using DEFAULT_RULES")
                    _RULE_CACHE[key] = DEFAULT_RULES
                    return DEFAULT_RULES
                _RULE_CACHE[key] = merged
                return merged
            except Exception as e:
                _VB_logging.error("Error loading %s: %s; using DEFAULT_RULES", c, e)
                _RULE_CACHE[key] = DEFAULT_RULES
                return DEFAULT_RULES
    _VB_logging.error("Rule pack not found for %s; using DEFAULT_RULES", path)
    return DEFAULT_RULES

# Minimal back-compat validator (only define if missing)
from typing import Iterable as _VB_Iter
if not callable(globals().get("validate_feasibility")):
    def _vb_to_float(x: _VB_Any, default: float = 0.0) -> float:
        try: return float(x)
        except Exception: return default
    def _vb_pairing_id(p: _VB_Dict[str, _VB_Any]) -> str:
        return str(p.get("pairing_id") or p.get("id") or p.get("name") or p.get("uid") or "UNKNOWN")
    def _vb_extract_rest_hours(p: _VB_Dict[str, _VB_Any]) -> float:
        for k in ("rest_hours","restHours","rest","min_rest_hours","minimum_rest_hours"):
            if k in p: return _vb_to_float(p[k], 0.0)
        for k in ("duty","summary","meta"):
            v = p.get(k); 
            if isinstance(v, dict):
                hh = v.get("rest_hours") or v.get("restHours")
                if hh is not None: return _vb_to_float(hh, 0.0)
        return 0.0
    def validate_feasibility(pairings: _VB_Iter[_VB_Dict[str,_VB_Any]], rules: _VB_Dict[str,_VB_Any] | None = None, context: _VB_Dict[str,_VB_Any] | None = None):
        out: list[_VB_Dict[str,_VB_Any]] = []
        for p in pairings or []:
            if not isinstance(p, dict): continue
            if _vb_extract_rest_hours(p) < 10.0:
                out.append({"id":"rest_min_10","pairing_id":_vb_pairing_id(p),"reason":"Rest < 10h","check":"pairing.rest_hours >= 10","severity":"hard"})
        return out

# ------------------------------------------------------------
# Recursive deep-merge + multi-pack support (back-compat safe)
# ------------------------------------------------------------
from typing import Sequence as _VB_Seq

# deep merge utility (dicts only); overlay wins for scalars/lists
try:
    _vb_deep_update  # type: ignore[name-defined]
except NameError:
    def _vb_deep_update(base: dict, overlay: dict) -> dict:
        for k, v in (overlay or {}).items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                _vb_deep_update(base[k], v)
            else:
                base[k] = v
        return base

# Keep a handle to the existing *single-path* loader we already have
try:
    _vb_single_loader = load_rule_pack  # type: ignore[name-defined]
except Exception:  # pragma: no cover
    _vb_single_loader = None  # type: ignore

def load_rule_pack(path: str | _VB_Seq[str], force_reload: bool = False):  # type: ignore[override]
    """
    Extended loader:
      - If 'path' is a string: delegate to the existing single-pack loader.
      - If 'path' is a sequence of paths: load each pack, then deep-merge
        the resulting dicts so nested rule fields are preserved.
    Always returns a unified {"hard": [...], "soft": [...]} and falls back
    to DEFAULT_RULES if needed.
    """
    # single pack: use the existing stable implementation
    if not isinstance(path, (list, tuple)):
        if _vb_single_loader is not None:
            return _vb_single_loader(path, force_reload=force_reload)  # type: ignore[misc]
        # Extreme fallback
        return _vb_load_default_rules_from_file()

    # multi-pack: deep-merge all, then normalize shape
    acc: dict = {}
    for p in path:
        try:
            d = _vb_single_loader(p, force_reload=force_reload) if _vb_single_loader else {}
        except Exception:
            d = {}
        acc = _vb_deep_update(acc or {}, d or {})

    merged = _vb_merge_rule_dict(acc)
    return merged if merged.get("hard") else DEFAULT_RULES

# ------------------------------------------------------------
# Optional concurrent validation wrapper (back-compat safe)
# ------------------------------------------------------------
import os as _VB_os
import concurrent.futures as _VB_fut
from typing import Any as _VB_Any, Dict as _VB_Dict, List as _VB_List

# Keep a handle to the existing sequential validator before we override
try:
    _vb_validate_feasibility_seq = validate_feasibility  # type: ignore[name-defined]
except Exception:  # pragma: no cover
    def _vb_validate_feasibility_seq(pairings, rules=None, context=None):  # type: ignore[unused-ignore]
        # Absolute fallback: sequential no-ops
        return []

def _vb_normalize_pairings_for_validate(raw: _VB_Any) -> _VB_List[_VB_Dict[str, _VB_Any]]:
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, dict)]
    if isinstance(raw, dict):
        # allow {"id": {…}} maps
        return [p if isinstance(p, dict) else {} for p in raw.values()]
    return []

def validate_feasibility(pairings, rules=None, context=None):  # type: ignore[override]
    """
    Back-compat wrapper around the existing sequential validator.
    Runs sequentially by default. Enable concurrency by either:
      - setting context["concurrency"] truthy or
      - exporting env VALIDATE_CONCURRENCY=1
    """
    items = _vb_normalize_pairings_for_validate(pairings)
    ctx = context or {}
    flag = False
    try:
        flag = bool(ctx.get("concurrency")) or str(_VB_os.getenv("VALIDATE_CONCURRENCY", "0")).lower() in ("1","true","yes","on")
    except Exception:
        flag = False

    if not flag or len(items) <= 1:
        # Call the original sequential implementation
        try:
            return _vb_validate_feasibility_seq(items, rules, ctx)
        except TypeError:
            try:
                return _vb_validate_feasibility_seq(items, rules)
            except TypeError:
                return _vb_validate_feasibility_seq(items)

    # Concurrent fan-out: call the original sequential validator per pairing
    max_workers = int(ctx.get("max_workers") or _VB_os.getenv("VALIDATE_MAX_WORKERS") or 4)
    results: _VB_List[_VB_Dict[str, _VB_Any]] = []
    with _VB_fut.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_vb_validate_feasibility_seq, [p], rules, ctx) for p in items]
        for fu in futs:
            try:
                vs = fu.result()
                if isinstance(vs, list):
                    results.extend(vs)
            except Exception:
                # If a worker fails, skip that item (keeps endpoint robust)
                pass
    return results
=======

        # --- Pilot hard constraints --------------------------------------
        conflict = _check_days_off(p.get("days", []), requested_off)
        if conflict:
            violations.append({
                "pairing_id": pid,
                "violation": f"Works on requested day off: {conflict}",
            })
            ok = False

        red_eye_flag = p.get("is_red_eye", p.get("redeye"))
        if hard.no_red_eyes and red_eye_flag:
            violations.append({
                "pairing_id": pid,
                "violation": "Red eye trip not allowed",
            })
            ok = False

        if hard.max_duty_hours_per_day and p.get("duty_hours", 0) > hard.max_duty_hours_per_day:
            violations.append({
                "pairing_id": pid,
                "violation": f"Duty hours exceed pilot limit {hard.max_duty_hours_per_day}",
            })
            ok = False

        # --- FAR 117 legality -------------------------------------------
        report = p.get("report_time")
        if report is not None:
            max_duty = rules.get_max_duty_hours(report)
            if p.get("duty_hours", 0) > max_duty:
                violations.append({
                    "pairing_id": pid,
                    "violation": f"Duty {p.get('duty_hours')}h exceeds FAR117 limit {max_duty}h",
                })
                ok = False

        rest = p.get("rest_hours")
        if rest is not None:
            min_rest = rules.get_min_rest(p.get("duty_hours", 0))
            if rest < min_rest:
                violations.append({
                    "pairing_id": pid,
                    "violation": f"Rest {rest}h below FAR117 minimum {min_rest}h",
                })
                ok = False

        # --- Union contract checks --------------------------------------
        base = bundle.context.base
        limit_map = rules.union.get("max_block_hours_per_base", {})
        max_block = limit_map.get(base, limit_map.get("default"))
        if max_block is not None and p.get("block_hours", 0) > max_block:
            violations.append({
                "pairing_id": pid,
                "violation": f"Block hours exceed base limit {max_block}",
            })
            ok = False

        if ok:
            feasible.append(p)

    # schedule wide check for days off
    days_off_count = len(requested_off)
    min_days = rules.union.get("min_days_off_per_month")
    if min_days and days_off_count < min_days:
        violations.append({
            "pairing_id": None,
            "violation": f"Minimum days off not met ({days_off_count} < {min_days})",
        })

    stats = {
        "total_pairings": len(pairings),
        "feasible_count": len(feasible),
        "days_off": days_off_count,
    }

    return {"violations": violations, "feasible_pairings": feasible, "stats": stats}

>>>>>>> Add Flask dependencies and Replit DB fallback
