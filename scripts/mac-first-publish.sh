#!/usr/bin/env bash
set -euo pipefail

KEY="$HOME/.ssh/richmackos_deploy"
HOST="ubuntu@3.129.79.249"

test -f "$KEY" || { echo "ERROR: $KEY missing" >&2; exit 1; }

# Install/update the versioned generic server-side deployment wrapper.
cat scripts/richdeploy-server.sh | ssh -o IdentitiesOnly=yes -i "$KEY" "$HOST" \
  'sudo tee /usr/local/bin/richdeploy >/dev/null && sudo chmod +x /usr/local/bin/richdeploy && /usr/local/bin/richdeploy --help 2>/dev/null || true'

# Create/configure the GitHub repository, secrets, wiki, discussions, issues,
# and perform the first push. The first push triggers CI/CD.
./scripts/github-bootstrap.sh
