#!/usr/bin/env bash
set -euo pipefail
# Run on Lightsail only. This patches the known Georgia DB backup filename in
# the generic richdeploy wrapper if the older name is present.
FILE=/usr/local/bin/richdeploy
sudo grep -q 'DB_FILE="data/richmack_georgia.db"' "$FILE" || {
  echo 'No old Georgia DB filename found; nothing to patch.'
  exit 0
}
sudo sed -i 's|DB_FILE="data/richmack_georgia.db"|DB_FILE="data/georgia.db"|' "$FILE"
echo 'Updated richdeploy Georgia DB backup path to data/georgia.db'
