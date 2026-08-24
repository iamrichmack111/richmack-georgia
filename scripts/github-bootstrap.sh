#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-iamrichmack111}"
REPO="${REPO:-richmack-georgia}"
VISIBILITY="${VISIBILITY:-public}"
DESCRIPTION="Evergreen Georgia geography and Georgia Studies learning platform for ages 9–14 with interactive maps, critical-thinking coursework, games, assignments, parent controls, grade exports, and skill analytics."
HOMEPAGE="https://georgia.richmackos.com"

command -v gh >/dev/null || { echo 'gh CLI is required'; exit 1; }
gh auth status

if ! gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  gh repo create "$OWNER/$REPO" --$VISIBILITY --description "$DESCRIPTION" --homepage "$HOMEPAGE" --source=. --remote=origin --push
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "git@github.com:$OWNER/$REPO.git"
  git push -u origin main
fi

gh repo edit "$OWNER/$REPO" \
  --description "$DESCRIPTION" \
  --homepage "$HOMEPAGE" \
  --enable-issues \
  --enable-wiki \
  --enable-discussions

echo 'Setting Actions deployment secrets...'
gh secret set RICHMACK_DEPLOY_KEY --repo "$OWNER/$REPO" < "$HOME/.ssh/richmackos_deploy"
printf '%s' '3.129.79.249' | gh secret set RICHMACK_DEPLOY_HOST --repo "$OWNER/$REPO"
printf '%s' 'ubuntu' | gh secret set RICHMACK_DEPLOY_USER --repo "$OWNER/$REPO"

echo 'GitHub repository and deployment secrets configured.'
