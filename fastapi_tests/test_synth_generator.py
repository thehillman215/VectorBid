from datetime import date
from pathlib import Path

from tools.pbs_synth import cli
from tools.pbs_synth.generator import generate_pairings


def test_generate_deterministic() -> None:
    month = date(2025, 9, 1)
    first = generate_pairings(month, "EWR", "73N", seed=42)
    second = generate_pairings(month, "EWR", "73N", seed=42)
    assert first == second


def test_cli_writes_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    cli.main(
        [
            "--month",
            "2025-09",
            "--base",
            "EWR",
            "--fleet",
            "73N",
            "--out",
            str(out_dir),
            "--seed",
            "42",
        ]
    )
    expected = {
        "pairings.csv",
        "trips.csv",
        "pairings.jsonl",
        "trips.jsonl",
    }
    assert expected == {p.name for p in out_dir.iterdir()}
