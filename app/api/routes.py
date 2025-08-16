# --- 1) Helpers for export location + atomic writer --------------------------
mkdir -p app/utils app/export
cat > app/utils/env.py <<'PY'
from __future__ import annotations
import os
from pathlib import Path

def export_dir() -> Path:
    """
    Root directory for persisted exports.
    ENV override: EXPORT_DIR
    Default: <repo_root>/exports
    """
    p = os.environ.get("EXPORT_DIR")
    if p:
        return Path(p).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "exports"
PY

cat > app/export/__init__.py <<'PY'
# package marker
PY

cat > app/export/storage.py <<'PY'
from __future__ import annotations
from pathlib import Path
from typing import Dict, Union
import json, os, re

from app.models import BidLayerArtifact
from app.security.api_key import require_api_key
from app.generate.layers import _canonical_sha256  # keep hash consistent

ArtifactLike = Union[BidLayerArtifact, Dict]

_AIRLINE_RE = re.compile(r"^[A-Z0-9_-]{2,8}$")
_MONTH_RE   = re.compile(r"^\d{4}-\d{2}$")

def _to_dict(a: ArtifactLike) -> Dict:
    return a.model_dump() if isinstance(a, BidLayerArtifact) else dict(a)

def _sanitize_airline(v: str | None) -> str:
    v = (v or "UNK").upper().strip()
    return v if _AIRLINE_RE.fullmatch(v) else "UNK"

def _sanitize_month(v: str | None) -> str:
    v = (v or "0000-00").strip()
    return v if _MONTH_RE.fullmatch(v) else "0000-00"

def _compute_hash(data: Dict) -> str:
    core = {k: v for k, v in data.items() if k not in {"export_hash", "lint"}}
    return _canonical_sha256(core)

def write_artifact(artifact: ArtifactLike, base_dir: Path) -> Path:
    """
    Persist artifact as exports/{AIRLINE}/{YYYY-MM}/{hash}.json
    - atomic write (temp file + os.replace)
    - idempotent (same path for same content)
    """
    data = _to_dict(artifact)
    export_hash = data.get("export_hash") or _compute_hash(data)
    if data.get("export_hash") != export_hash:
        data["export_hash"] = export_hash

    airline = _sanitize_airline(data.get("airline"))
    month   = _sanitize_month(data.get("month"))

    out_dir = (Path(base_dir).expanduser().resolve() / airline / month)
    out_dir.mkdir(parents=True, exist_ok=True)

    target = out_dir / f"{export_hash}.json"
    tmp = target.with_suffix(target.suffix + ".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)

    return target
PY

# --- 2) Patch app/api/routes.py automatically (no manual snippet pasting) ----
python - <<'PY'
from pathlib import Path
import re

p = Path("app/api/routes.py")
txt = p.read_text()

def ensure_import(txt, pattern, replacement):
    if not re.search(pattern, txt):
        # Put new import after the first existing 'from app.' import if present,
        # else right after the 'from typing' / 'from fastapi' block.
        lines = txt.splitlines()
        inserted = False
        for i, line in enumerate(lines):
            if line.startswith("from app.") or line.startswith("import app"):
                lines.insert(i, replacement)
                inserted = True
                break
        if not inserted:
            # find a sensible header anchor
            for i, line in enumerate(lines[:25]):
                if line.startswith("from fastapi") or line.startswith("from typing"):
                    anchor = i
            try:
                lines.insert(anchor+1, replacement)
            except:
                lines.insert(0, replacement)
        return "\n".join(lines)
    return txt

# 2a) add HTTPException to fastapi import (or add a new import if needed)
if "from fastapi import APIRouter, HTTPException, Depends" not in txt:
    txt = re.sub(
        r"from fastapi import APIRouter, HTTPException, Depends\b(?!,)",
        "from fastapi import APIRouter, HTTPException, Depends",
        txt
    )

if "HTTPException" not in txt and "from fastapi import" not in txt:
    txt = "from fastapi import HTTPException\n" + txt

# 2b) add export helpers imports
txt = ensure_import(txt,
    r"from app\.export\.storage import write_artifact",
    "from app.export.storage import write_artifact"
)
txt = ensure_import(txt,
    r"from app\.utils\.env import export_dir",
    "from app.utils.env import export_dir"
)

# 2c) add /export route if missing
if '@router.post("/export")' not in txt:
    block = '''
@router.post("/export", tags=["Generate"])
def export(payload: Dict[str, Any]) -> Dict[str, Any]:
    artifact = payload.get("artifact")
    if not artifact:
        raise HTTPException(status_code=400, detail="artifact required")
    try:
        base = export_dir()
        path = write_artifact(artifact, base)
        return {"export_path": str(path), "export_hash": path.stem}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"export failed: {e}") from e
'''
    if txt.endswith("
", _auth=Depends(require_api_key)):
        txt = txt + block.lstrip("\n")
    else:
        txt = txt + "\n" + block.lstrip("\n")

p.write_text(txt)
print("Patched app/api/routes.py")
PY

# --- 3) Optional: tiny endpoint test to prove behavior -----------------------
cat > fastapi_tests/test_export_endpoint.py <<'PY'
from fastapi.testclient import TestClient
from app.main import app
from app.generate import layers as gen_layers
import json, pathlib

def test_export_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(gen_layers, "_next_month_tag", lambda dt: "2025-09")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))

    client = TestClient(app)

    DATA = {"pairings":[
      {"id":"P1","layover_city":"SAN","redeye":False,"rest_hours":12},
      {"id":"P2","layover_city":"SJU","redeye":False,"rest_hours":11},
      {"id":"P3","layover_city":"XXX","redeye":True,"rest_hours":9}
    ]}
    pref = {
      "pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO","equip":["73G"],
      "hard_constraints":{"no_red_eyes": True},
      "soft_prefs":{"layovers":{"prefer":["SAN","SJU"],"weight":1.0}}
    }
    ctx = {"ctx_id":"ctx-u1","pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO",
           "equip":["73G"],"seniority_percentile":0.5,"commuting_profile":{},
           "default_weights":{"layovers":1.0}}

    fb = {
        "feature_bundle": {
            "context": ctx,
            "preference_schema": pref,
            "analytics_features": {
                "base_stats": {"SAN": {"award_rate": 0.65}, "SJU": {"award_rate": 0.55}}
            },
            "compliance_flags": {},
            "pairing_features": DATA,
        },
        "K": 5,
    }

    topk = client.post("/optimize", json=fb).json()["candidates"]
    artifact = client.post(
        "/generate_layers",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    ).json()["artifact"]

    r1 = client.post("/export", json={"artifact": artifact})
    assert r1.status_code == 200
    out1 = r1.json()
    p1 = pathlib.Path(out1["export_path"])
    assert p1.exists()

    saved = json.loads(p1.read_text())
    assert saved["export_hash"] == artifact["export_hash"]

    r2 = client.post("/export", json={"artifact": artifact})
    assert r2.status_code == 200
    assert r2.json()["export_path"] == out1["export_path"]
PY

# --- 4) Ignore local exports, run tests, commit, push ------------------------
grep -qxF 'exports/' .gitignore || echo 'exports/' >> .gitignore

PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -c pytest.ini

git add app/utils/env.py app/export/__init__.py app/export/storage.py app/api/routes.py \
        fastapi_tests/test_export_endpoint.py .gitignore
git commit -m "feat(export): add /export endpoint (atomic, deterministic) + helpers"
git push origin feat/fastapi-v0.3-guardrails