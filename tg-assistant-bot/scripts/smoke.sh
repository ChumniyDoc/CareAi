#!/usr/bin/env bash
set -euo pipefail

ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

root_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
if [[ "${root_code}" != "200" && "${root_code}" != "302" && "${root_code}" != "307" ]]; then
  echo "Root endpoint failed with ${root_code}"
  exit 1
fi
curl -fsSL http://localhost:8080/healthz >/dev/null
curl -fsSL http://localhost:8080/readyz >/dev/null
curl -fsSL -u "${ADMIN_USER}:${ADMIN_PASSWORD}" http://localhost:8080/admin/stats.json >/dev/null
curl -fsSL -u "${ADMIN_USER}:${ADMIN_PASSWORD}" -X POST http://localhost:8080/admin/selftest >/dev/null

docker compose exec -T app curl -fsSL http://ollama:11434/api/tags >/dev/null

docker compose exec -T db psql -U postgres -d tg_assistant -c "select 1;" >/dev/null

printf "Smoke checks passed.\n"
