"""Command line interface for synthetic dataset generator."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .emit import write_csv, write_jsonl
from .generator import generate_pairings


def _parse_month(value: str) -> date:
    return date.fromisoformat(f"{value}-01")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic PBS datasets")
    parser.add_argument("--month", required=True, help="Target month in YYYY-MM format")
    parser.add_argument("--base", required=True, help="Pilot base code")
    parser.add_argument("--fleet", required=True, help="Fleet code")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    args = parser.parse_args(argv)

    month = _parse_month(args.month)
    pairings = generate_pairings(month=month, base=args.base, fleet=args.fleet, seed=args.seed)
    write_csv(pairings, args.out)
    write_jsonl(pairings, args.out)


if __name__ == "__main__":
    main()
