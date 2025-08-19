#!/usr/bin/env python3
"""Load local fixture data for demos and tests.

This script copies fixture bid packets and trips into the local
``bids`` directory and seeds the Replit DB profile and preferences for a
``demo_pilot`` user. Running it multiple times is safe.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.lib.preferences_manager import preferences_manager  # noqa: E402
from src.lib.services.db import save_profile  # noqa: E402

DEFAULT_FIXTURE = ROOT / "fixtures" / "UAL" / "2025-09"
BIDS_DIR = ROOT / "bids"


def load_fixture(fixture_dir: str | Path = DEFAULT_FIXTURE) -> None:
    """Load fixture data into the local environment.

    Args:
        fixture_dir: Directory containing fixture files.
    """
    path = Path(fixture_dir)
    if not path.exists():
        raise FileNotFoundError(f"fixture directory not found: {path}")

    BIDS_DIR.mkdir(exist_ok=True)

    # Copy bid packet JSON
    bid_src = path / "bid_packet.json"
    if bid_src.exists():
        bid_dest = BIDS_DIR / f"{path.parent.name}_{path.name}.json"
        if not bid_dest.exists():
            shutil.copy(bid_src, bid_dest)
            print(f"copied bid packet to {bid_dest}")
        else:
            print(f"bid packet already present at {bid_dest}")

    # Copy trips JSONL
    trips_src = path / "trips.jsonl"
    if trips_src.exists():
        trips_dest = BIDS_DIR / f"{path.parent.name}_{path.name}_trips.jsonl"
        if not trips_dest.exists():
            shutil.copy(trips_src, trips_dest)
            print(f"copied trips to {trips_dest}")
        else:
            print(f"trips already present at {trips_dest}")

    # Seed profile
    profile_path = path / "profile.json"
    if profile_path.exists():
        try:
            with profile_path.open("r", encoding="utf-8") as f:
                profile = json.load(f)
            save_profile("demo_pilot", profile)
            print("seeded demo_pilot profile")
        except Exception as exc:  # pragma: no cover - best effort
            print(f"skipping profile seed: {exc}")

    # Seed preferences
    preferences_path = path / "preferences.json"
    if preferences_path.exists():
        try:
            with preferences_path.open("r", encoding="utf-8") as f:
                prefs = json.load(f)
            preferences_manager.update_preferences("demo_pilot", prefs)
            print("seeded demo_pilot preferences")
        except Exception as exc:  # pragma: no cover - best effort
            print(f"skipping preferences seed: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load VectorBid fixture data")
    parser.add_argument(
        "fixture_dir",
        nargs="?",
        default=DEFAULT_FIXTURE,
        help="Fixture directory to load",
    )
    args = parser.parse_args()
    load_fixture(args.fixture_dir)
