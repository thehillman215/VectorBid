from pathlib import Path

from app.services.pbs_parser.reader import load_csv, load_jsonl

GOLDENS = Path("data/goldens")


def test_load_csv_golden() -> None:
    pairings = load_csv(GOLDENS)
    assert len(pairings) == 1
    p = pairings[0]
    assert p.pairing_id == "EWR-73N-001"
    assert len(p.trips) == 2
    assert {t.destination for t in p.trips} == {"EWR"}


def test_load_jsonl_golden() -> None:
    pairings = load_jsonl(GOLDENS)
    assert len(pairings) == 1
    assert pairings[0].trips[0].pairing_id == "EWR-73N-001"
