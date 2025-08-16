#!/usr/bin/env python3
from __future__ import annotations
import cProfile, pstats, io, random, json, argparse, time
from fastapi.testclient import TestClient
from app.main import app

def make_bundle(n: int):
    cities = ["SAN","SJU","DEN","IAH","ORD","LAX","EWR"]
    random.seed(42)
    pairings = [{"id": f"P{i}",
                 "layover_city": cities[i % len(cities)],
                 "redeye": False if i % 11 else True,
                 "rest_hours": 12 if i % 13 else 9}
                for i in range(1, n+1)]
    DATA = {"pairings": pairings}
    pref = {"pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO","equip":["73G"],
            "hard_constraints":{"no_red_eyes": True},
            "soft_prefs":{"layovers":{"prefer":["SAN","SJU"],"weight":1.0}}}
    ctx = {"ctx_id":"ctx-u1","pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO",
           "equip":["73G"],"seniority_percentile":0.5,"commuting_profile":{},
           "default_weights":{"layovers":1.0}}
    bundle = {"context": ctx, "preference_schema": pref,
              "analytics_features":{"base_stats":{"SAN":{"award_rate":0.65},"SJU":{"award_rate":0.55}}},
              "compliance_flags": {}, "pairing_features": DATA}
    return bundle

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--dump", type=str, default="")
    args = ap.parse_args()

    client = TestClient(app)
    bundle = make_bundle(args.n)

    # Warm up validate (ensures any lazy setup is done)
    client.post("/validate", json={
        "preference_schema": bundle["preference_schema"],
        "context": bundle["context"],
        "pairings": bundle["pairing_features"],
    }).raise_for_status()

    pr = cProfile.Profile()
    pr.enable()
    t0 = time.time()
    for _ in range(args.runs):
        r = client.post("/optimize", json={"feature_bundle": bundle, "K": args.k})
        r.raise_for_status()
    t = time.time() - t0
    pr.disable()

    print(f"/optimize x{args.runs} for N={args.n}, K={args.k}: {t*1000:.1f} ms total")

    s = io.StringIO()
    stats = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    stats.print_stats(25)  # top 25
    print(s.getvalue())

    if args.dump:
        stats.dump_stats(args.dump)

if __name__ == "__main__":
    main()
