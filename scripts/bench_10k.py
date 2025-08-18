#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import time
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def _build_pairings(n: int) -> dict[str, Any]:
    # Deterministic but varied; mostly valid (no redeyes, rest >= 10)
    cities = ["SAN", "SJU", "DEN", "IAH", "ORD", "LAX", "EWR"]
    random.seed(42)
    pairings = []
    for i in range(1, n + 1):
        city = cities[i % len(cities)]
        pairings.append(
            {
                "id": f"P{i}",
                "layover_city": city,
                "redeye": False if i % 11 else True,  # rare violations
                "rest_hours": 12 if i % 13 else 9,  # rare violations
            }
        )
    return {"pairings": pairings}


def _pref() -> dict[str, Any]:
    return {
        "pilot_id": "u1",
        "airline": "UAL",
        "base": "EWR",
        "seat": "FO",
        "equip": ["73G"],
        "hard_constraints": {"no_red_eyes": True},
        "soft_prefs": {"layovers": {"prefer": ["SAN", "SJU"], "weight": 1.0}},
    }


def _ctx() -> dict[str, Any]:
    return {
        "ctx_id": "ctx-u1",
        "pilot_id": "u1",
        "airline": "UAL",
        "base": "EWR",
        "seat": "FO",
        "equip": ["73G"],
        "seniority_percentile": 0.5,
        "commuting_profile": {},
        "default_weights": {"layovers": 1.0},
    }


def _analytics() -> dict[str, Any]:
    # Keep tiny; optimizer just needs something plausible
    return {"base_stats": {"SAN": {"award_rate": 0.65}, "SJU": {"award_rate": 0.55}}}


def run_once(n: int, k: int) -> None:
    client = TestClient(app)
    pref = _pref()
    ctx = _ctx()
    pairings = _build_pairings(n)
    bundle = {
        "context": ctx,
        "preference_schema": pref,
        "analytics_features": _analytics(),
        "compliance_flags": {},
        "pairing_features": pairings,
    }

    timings = {}

    t0 = time.time()
    r = client.post(
        "/validate",
        json={"preference_schema": pref, "context": ctx, "pairings": pairings},
    )
    r.raise_for_status()
    timings["validate"] = time.time() - t0
    violations = r.json().get("violations", [])

    t0 = time.time()
    r = client.post("/optimize", json={"feature_bundle": bundle, "K": k})
    r.raise_for_status()
    timings["optimize"] = time.time() - t0
    topk = r.json()["candidates"]

    t0 = time.time()
    r = client.post("/strategy", json={"feature_bundle": bundle, "candidates": topk})
    r.raise_for_status()
    timings["strategy"] = time.time() - t0
    directives = r.json()["directives"]

    t0 = time.time()
    r = client.post(
        "/generate_layers", json={"feature_bundle": bundle, "candidates": topk}
    )
    r.raise_for_status()
    timings["generate_layers"] = time.time() - t0
    artifact = r.json()["artifact"]

    t0 = time.time()
    r = client.post("/lint", json={"artifact": artifact})
    r.raise_for_status()
    timings["lint"] = time.time() - t0
    lint = r.json()

    # Pretty summary
    total = sum(timings.values())
    print("\n=== VectorBid bench ===")
    print(f"pairings: {n:,}   K: {k}")
    for kstep in ["validate", "optimize", "strategy", "generate_layers", "lint"]:
        print(f"{kstep:16s} {timings[kstep] * 1000:8.1f} ms")
    print(f"{'total':16s} {total * 1000:8.1f} ms")

    if violations:
        print(f"violations: {len(violations)} (sample: {violations[:2]})")
    print(
        f"candidates: {len(topk)}; top 5 ids: {[c['candidate_id'] for c in topk[:5]]}"
    )
    print(
        f"artifact: month={artifact['month']} format={artifact['format']} hash={artifact['export_hash'][:12]}…"
    )
    if lint.get("errors"):
        print(f"lint.errors: {lint['errors']}")
    if lint.get("warnings"):
        print(f"lint.warnings (first 3): {lint['warnings'][:3]}")


def main():
    ap = argparse.ArgumentParser(
        description="Benchmark VectorBid pipeline on a large batch."
    )
    ap.add_argument(
        "--n", type=int, default=10_000, help="number of pairings to include"
    )
    ap.add_argument("--k", type=int, default=50, help="top-K candidates to return")
    args = ap.parse_args()
    run_once(args.n, args.k)


if __name__ == "__main__":
    main()
