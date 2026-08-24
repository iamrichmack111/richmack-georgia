#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"

trap 'rm -rf "$TMP"' EXIT

echo "Cloning Wiki..."
git clone "git@github.com:$OWNER/$REPO.wiki.git" "$TMP/wiki"

echo "Copying Wiki pages..."
rsync -a --delete \
  --exclude '.git/' \
  "$ROOT/wiki-seed/" \
  "$TMP/wiki/"

cd "$TMP/wiki"

git add -A

if git diff --cached --quiet; then
  echo "Wiki already up to date."
  exit 0
fi

git commit -m "docs: seed Richmack Georgia wiki"

BRANCH="$(git branch --show-current)"

echo "Pushing Wiki branch: $BRANCH"
git push origin "$BRANCH"

echo "✓ Wiki seeded successfully."
