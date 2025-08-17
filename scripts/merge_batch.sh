#!/usr/bin/env bash
set -euo pipefail

BASE_BRANCH="release/2025-08-17"
APP_IMPORT="${APP_IMPORT:-app.main:app}"
PORT="${PORT:-8000}"

git fetch --all --prune
git checkout "$BASE_BRANCH"
git pull --ff-only || true

i=0
while IFS= read -r line; do
  BRANCH=$(echo "$line" | awk '{print $1}')
  [[ -z "$BRANCH" ]] && continue
  i=$((i+1))
  echo "=== [$i] Merging $BRANCH into $BASE_BRANCH ==="
  if git merge --no-ff "origin/$BRANCH" -m "merge($BRANCH): roll into $BASE_BRANCH"; then
    echo "Running smoke..."
    APP_IMPORT="$APP_IMPORT" PORT="$PORT" scripts/smoke.sh
    tag="rc-$(date +%Y%m%d-%H%M%S)-${i}"
    git tag "$tag" -m "checkpoint after $BRANCH"
    git push && git push --tags
  else
    echo "Conflict with $BRANCH. Resolve or rebase origin/$BRANCH onto $BASE_BRANCH, then re-run."
    exit 1
  fi
done < merge_queue.txt

echo "All queued merges completed."
