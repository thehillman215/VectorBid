import csv
import datetime
import sys
from pathlib import Path

inv = Path("merge_inventory.csv")
if not inv.exists():
    print("merge_inventory.csv not found")
    sys.exit(1)

today = datetime.date.today().isoformat()
out_csv = Path(f"VectorBid_Merge_Queue_{today}.csv")
out_merge = Path("merge_queue.txt")
out_hold = Path("merge_hold.txt")

RESERVED = {"origin", "main", "master", "HEAD", "release", ""}


def guess_category(branch: str) -> str:
    b = branch.lower()
    if b.startswith(("fix/", "bugfix/", "hotfix/")):
        return "bugfix"
    if b.startswith(("infra/", "devops/", "ci/", "build/")):
        return "infra"
    if b.startswith(("depfu/", "dependabot/", "renovate/")):
        return "dep-bump"
    if b.startswith(("chore/", "docs/")):
        return "chore"
    if "experiment" in b or "spike" in b or b.startswith("exp/"):
        return "experiment"
    if b.startswith(("feat/", "feature/")):
        return "feature"
    return "feature"


def risk_level(ahead: int, behind: int, conflicts: str) -> str:
    score = ahead + 2 * behind + (10 if conflicts == "yes" else 0)
    return "low" if score <= 5 else ("medium" if score <= 20 else "high")


def strategy(category: str, conflicts: str, ahead: int) -> str:
    if category == "bugfix":
        return "squash"
    if category == "infra":
        return "rebase" if conflicts == "no" else "merge-commit"
    if category == "dep-bump":
        return "merge-commit"
    if category in ("chore", "docs"):
        return "squash"
    if category == "experiment":
        return "cherry-pick"
    if conflicts == "no" and ahead <= 25:
        return "rebase"
    return "merge-commit"


def decision(category: str, risk: str, conflicts: str) -> str:
    if category == "experiment":
        return "HOLD"
    if conflicts == "yes" and risk == "high":
        return "HOLD"
    return "MERGE"


rows = []
with inv.open() as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        b = (r.get("branch", "") or "").strip()
        if b in RESERVED or b.startswith("release/"):  # skip junk/reserved
            continue
        ahead = int(r.get("ahead", "0") or 0)
        behind = int(r.get("behind", "0") or 0)
        conflicts = (r.get("conflicts", "") or "").strip().lower()
        cat = guess_category(b)
        risk = risk_level(ahead, behind, conflicts)
        strat = strategy(cat, conflicts, ahead)
        dec = decision(cat, risk, conflicts)
        notes = []
        if conflicts == "yes":
            notes.append("rebase on release/2025-08-17 first")
        if cat == "feature":
            notes.append("gate behind flag if incomplete")
        rows.append(
            {
                "branch": b,
                "ahead_of_main": ahead,
                "behind_main": behind,
                "last_commit_date": r.get("last_commit", ""),
                "owner": r.get("author", ""),
                "category": cat,
                "risk": risk,
                "merge_strategy": strat,
                "conflicts_expected": conflicts,
                "test_status": "unknown",
                "ci_checks": "lint,type,unit,smoke",
                "flags_needed": "admin_portal" if "admin" in b.lower() else "",
                "notes": "; ".join(notes),
                "decision": dec,
                "target_window": ("Day 1" if risk == "low" and conflicts == "no" else "Day 2"),
            }
        )

# order queue
cat_order = {
    "bugfix": 0,
    "infra": 1,
    "chore": 2,
    "docs": 2,
    "feature": 3,
    "dep-bump": 4,
    "experiment": 5,
}
risk_order = {"low": 0, "medium": 1, "high": 2}
rows.sort(
    key=lambda x: (
        x["decision"] != "MERGE",
        cat_order.get(x["category"], 9),
        x["conflicts_expected"] == "yes",
        risk_order.get(x["risk"], 2),
        x["ahead_of_main"],
        x["behind_main"],
        x["branch"],
    )
)

fields = [
    "branch",
    "ahead_of_main",
    "behind_main",
    "last_commit_date",
    "owner",
    "category",
    "risk",
    "merge_strategy",
    "conflicts_expected",
    "test_status",
    "ci_checks",
    "flags_needed",
    "notes",
    "decision",
    "target_window",
]

with out_csv.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

with out_merge.open("w") as fm, out_hold.open("w") as fh:
    for r in rows:
        line = r["branch"]
        comment = f"# {r['category']} {r['risk']} {r['merge_strategy']}"
        if r["decision"] == "MERGE" and r["conflicts_expected"] == "no":
            fm.write(f"{line}  {comment}\n")
        elif r["decision"] == "MERGE" and r["conflicts_expected"] == "yes":
            fh.write(f"{line}  {comment}  # CONFLICT: rebase first\n")
        else:
            fh.write(f"{line}  {comment}  # {r['decision']}\n")

print(f"Wrote {out_csv}, merge_queue.txt, merge_hold.txt")
