from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models import FeatureBundle
from app.rules.models import HardRule, RulePack


def load_rule_pack(path: str) -> RulePack:
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
    pairings = bundle.pairing_features.get("pairings", [])
    violations: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    for p in pairings:
        ok = True
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
