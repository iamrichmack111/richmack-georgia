#!/usr/bin/env bash
set -euo pipefail

APP="${1:-arithmetic}"

case "$APP" in
  arithmetic|richmack-arithmetic)
    APP_DIR="/home/ubuntu/richmack-arithmetic"
    PORT="5055"
    DB_FILE="data/richmack_arithmetic.db"
    BACKUP_PREFIX="richmack_arithmetic"
    SERVICE="richmath"
    LABEL="Richmack Arithmetic"
    ;;
  georgia|richmack-georgia)
    APP_DIR="/home/ubuntu/richmack-georgia"
    PORT="5075"
    DB_FILE="data/georgia.db"
    BACKUP_PREFIX="richmack_georgia"
    SERVICE="richmack-georgia"
    LABEL="Richmack Georgia"
    ;;
  *)
    echo "Unknown app: $APP" >&2
    echo "Usage: richdeploy {arithmetic|georgia}" >&2
    exit 2
    ;;
esac

cd "$APP_DIR"
echo "== $LABEL deploy =="
test -f .env || { echo "ERROR: $APP_DIR/.env missing" >&2; exit 1; }
mkdir -p data backups

if [ -f "$DB_FILE" ]; then
  BACKUP="backups/${BACKUP_PREFIX}-$(date +%Y%m%d-%H%M%S).db"
  cp "$DB_FILE" "$BACKUP"
  echo "Database backup: $BACKUP"
fi

if [ -d app ]; then
  python3 -m py_compile app/*.py
fi
if [ -f run.py ]; then
  python3 -m py_compile run.py
fi

docker compose build
docker compose up -d --remove-orphans

READY=0
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 2
done

if [ "$READY" -ne 1 ]; then
  docker compose ps
  if docker compose config --services | grep -qx "$SERVICE"; then
    docker compose logs --tail=120 "$SERVICE"
  else
    docker compose logs --tail=120
  fi
  exit 1
fi

curl -fsS "http://127.0.0.1:${PORT}/health"
echo
echo "✓ $LABEL is healthy."
