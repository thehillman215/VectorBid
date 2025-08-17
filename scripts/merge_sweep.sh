#!/usr/bin/env bash
set -euo pipefail

PR_LIST="${PR_LIST:-}"             # e.g. "25 31 28 33 29"
BASE_BRANCH="${BASE_BRANCH:-origin/main}"  # use the remote tip by default
ROLLUP_BRANCH="${ROLLUP_BRANCH:-merge-sweep/$(date +%Y%m%d)-main}"

if [[ -z "$PR_LIST" ]]; then
  echo "Set PR_LIST=\"<ids>\" (e.g., PR_LIST=\"25 31 28 33 29\") and rerun."; exit 2
fi

git fetch --all --prune

# Create/overwrite rollup from the exact base commit (works for local or remote refs)
BASE_COMMIT="$(git rev-parse --verify "${BASE_BRANCH}^{commit}")"
git checkout -B "$ROLLUP_BRANCH" "$BASE_COMMIT"

LOG="rollup_log_$(date +%Y%m%d_%H%M%S).txt"
OK="rollup_ok.txt"; : > "$OK"
HOLD="rollup_hold.txt"; : > "$HOLD"

i=0
for ID in $PR_LIST; do
  i=$((i+1))
  echo "=== [$i] PR #$ID ===" | tee -a "$LOG"

  # fetch PR head as local branch pr/<id> (works for forks)
  if ! git fetch origin "pull/${ID}/head:pr/${ID}"; then
    echo "#$ID fetch_failed" | tee -a "$LOG"; echo "$ID fetch_failed" >> "$HOLD"; continue
  fi

  if git merge --no-ff "pr/${ID}" -m "rollup: merge PR #${ID} into ${ROLLUP_BRANCH}"; then
    # Smoke + tests
    set +e
    scripts/smoke.sh; SMOKE=$?
    pytest -q; TEST=$?
    set -e
    if [[ $SMOKE -eq 0 && $TEST -eq 0 ]]; then
      echo "#$ID PASS" | tee -a "$LOG"; echo "$ID" >> "$OK"
      git tag -f "rollup-pr-${ID}" -m "Merged in rollup"
    else
      echo "#$ID FAIL (smoke=$SMOKE test=$TEST). Reverting..." | tee -a "$LOG"
      git revert --no-edit HEAD
      echo "$ID failed_tests" >> "$HOLD"
    fi
  else
    echo "#$ID CONFLICT. Aborting merge." | tee -a "$LOG"
    git merge --abort || true
    echo "$ID conflicts" >> "$HOLD"
    echo "Resolve conflicts on $ROLLUP_BRANCH, commit, then rerun with remaining PRs."
    break
  fi
done

echo "OK:   $(tr '\n' ' ' < \"$OK\" 2>/dev/null)" | tee -a "$LOG"
echo "HOLD: $(tr '\n' ' ' < \"$HOLD\" 2>/dev/null)" | tee -a "$LOG"
echo "Rollup branch: $ROLLUP_BRANCH"
