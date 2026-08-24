#!/usr/bin/env bash
set -euo pipefail

# One-time Mac-side publication entry point.
# Assumes gh auth login has already been completed and the Lightsail deploy
# key exists at ~/.ssh/richmackos_deploy.

# Fix the production richdeploy DB backup filename first.
ssh -o IdentitiesOnly=yes \
  -i "$HOME/.ssh/richmackos_deploy" \
  ubuntu@3.129.79.249 \
  "sudo sed -i 's|DB_FILE=\"data/richmack_georgia.db\"|DB_FILE=\"data/georgia.db\"|' /usr/local/bin/richdeploy; grep -A8 -B2 'georgia|richmack-georgia' /usr/local/bin/richdeploy || true"

./scripts/github-bootstrap.sh
