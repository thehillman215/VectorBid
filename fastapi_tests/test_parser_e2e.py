import json
from pathlib import Path

from app.services.pbs_parser.optimizer import optimize
from app.services.pbs_parser.reader import load_csv


def test_optimize_snapshot() -> None:
    pairings = load_csv(Path("data/goldens"))
    result = optimize(pairings)
    snapshot = json.loads(
        Path("fastapi_tests/goldens/optimizer_snapshot.json").read_text()
    )
    assert result == snapshot
