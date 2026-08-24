#!/usr/bin/env bash
set -euo pipefail
OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

git clone "git@github.com:$OWNER/$REPO.wiki.git" "$TMP/wiki"
rsync -a --delete wiki-seed/ "$TMP/wiki/"
cd "$TMP/wiki"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "docs: seed Richmack Georgia wiki"
  git push origin master || git push origin main
fi
