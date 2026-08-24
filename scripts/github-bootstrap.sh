#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"
VISIBILITY="${VISIBILITY:-public}"
DESCRIPTION="Evergreen Georgia geography and Georgia Studies learning platform for ages 9–14 with interactive maps, critical-thinking coursework, games, assignments, parent controls, grade exports, and skill analytics."
HOMEPAGE="https://georgia.richmackos.com"
FULL="$OWNER/$REPO"

command -v gh >/dev/null || { echo 'ERROR: gh CLI is required.'; exit 1; }
command -v jq >/dev/null || { echo 'ERROR: jq is required.'; exit 1; }
gh auth status

# Create the remote without pushing yet so Actions secrets are available on
# the very first main-branch push.
if ! gh repo view "$FULL" >/dev/null 2>&1; then
  gh repo create "$FULL" --$VISIBILITY --description "$DESCRIPTION" --homepage "$HOMEPAGE"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "git@github.com:$FULL.git"
else
  git remote add origin "git@github.com:$FULL.git"
fi

gh repo edit "$FULL" \
  --description "$DESCRIPTION" \
  --homepage "$HOMEPAGE" \
  --enable-issues \
  --enable-wiki \
  --enable-discussions \
  --add-topic georgia \
  --add-topic geography \
  --add-topic education \
  --add-topic flask \
  --add-topic leaflet \
  --add-topic homeschool \
  --add-topic critical-thinking

echo 'Setting Actions deployment secrets before first push...'
test -f "$HOME/.ssh/richmackos_deploy" || { echo 'ERROR: ~/.ssh/richmackos_deploy missing'; exit 1; }
gh secret set RICHMACK_DEPLOY_KEY --repo "$FULL" < "$HOME/.ssh/richmackos_deploy"
printf '%s' '3.129.79.249' | gh secret set RICHMACK_DEPLOY_HOST --repo "$FULL"
printf '%s' 'ubuntu' | gh secret set RICHMACK_DEPLOY_USER --repo "$FULL"

echo 'Pushing reconstructed history and CI/CD...'
git push -u origin main

echo 'Backfilling resolved issues...'
./scripts/backfill-github-community.sh

echo 'Seeding wiki...'
./scripts/seed-wiki.sh

echo 'Seeding discussions...'
./scripts/seed-discussions.sh

echo
echo "Repository: https://github.com/$FULL"
echo "Production: $HOMEPAGE"
echo 'Future normal update: git add/commit/push -> GitHub Actions -> richdeploy georgia -> health check'
