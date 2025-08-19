import hashlib
import json
from pathlib import Path

from app.pbs.export import append_hash, write_json


def test_append_hash(tmp_path: Path) -> None:
    artifact = {
        "airline": "UAL",
        "format": "PBS2",
        "month": "2025-09",
        "layers": [],
        "lint": {},
    }
    data = append_hash(artifact)
    canonical = json.dumps(
        artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert data["export_hash"] == expected

    out_file = tmp_path / "artifact.json"
    write_json(artifact, out_file)
    saved = json.loads(out_file.read_text())
    assert saved["export_hash"] == expected
