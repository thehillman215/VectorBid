#!/usr/bin/env bash
set -euo pipefail
git fetch --all --prune
OUT="merge_inventory.csv"
echo "branch,ahead,behind,last_commit,author,conflicts" > "$OUT"
BASE="origin/release/2025-08-17"
git rev-parse --verify "$BASE" >/dev/null 2>&1 || BASE="origin/main"
for rb in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -Ev 'origin/(HEAD|main|master|release/)'); do
  b="${rb#origin/}"
  read A B < <(git rev-list --left-right --count origin/main...$rb)
  last=$(git log -1 --pretty='%cI' "$rb")
  auth=$(git log -1 --pretty='%an' "$rb")
  git reset --hard "$BASE" >/dev/null 2>&1
  if git merge --no-ff --no-commit "$rb" >/dev/null 2>&1; then
    conflicts=no
  else
    conflicts=yes
  fi
  git merge --abort >/dev/null 2>&1 || true
  echo "$b,$A,$B,$last,$auth,$conflicts" >> "$OUT"
done
echo "Wrote $OUT"
