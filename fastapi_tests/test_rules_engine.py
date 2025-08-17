import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.rules.engine import load_rule_pack, DEFAULT_RULES


def test_load_rule_pack_merge_success(tmp_path):
    data = {
        "far117": {"hard": [{"id": "A"}], "soft": [{"id": "S1"}]},
        "union": {"hard": [{"id": "B"}], "soft": [{"id": "S2"}]},
    }
    f = tmp_path / "rules.yml"
    f.write_text(yaml.safe_dump(data))
    merged = load_rule_pack(str(f))
    assert merged == {
        "hard": [{"id": "A"}, {"id": "B"}],
        "soft": [{"id": "S1"}, {"id": "S2"}],
    }


def test_load_rule_pack_missing_keys(tmp_path, caplog):
    data = {"far117": {"hard": []}}
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
