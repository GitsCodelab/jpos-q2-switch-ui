#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

log() {
  printf '[fraud-e2e] %s\n' "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-60}"
  local sleep_seconds="${3:-2}"
  local i=1
  while [[ $i -le $attempts ]]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_seconds"
    i=$((i + 1))
  done
  return 1
}

require_cmd docker
require_cmd curl
require_cmd mvn

log "Starting required containers (postgres, switch, backend, frontend)"
docker compose up -d --build jpos-postgresql switch jpos-backend jpos-frontend >/dev/null

log "Waiting for backend health endpoint"
if ! wait_for_url "http://localhost:8000/health" 90 2; then
  echo "Backend did not become healthy in time" >&2
  exit 1
fi

log "Waiting for frontend shell"
if ! wait_for_url "http://localhost:5173" 90 2; then
  echo "Frontend did not become reachable in time" >&2
  exit 1
fi

if [[ ! -f .cp.txt ]]; then
  log "Generating .cp.txt for ISO simulator"
  mvn -q -DskipTests dependency:build-classpath -Dmdep.outputFile=.cp.txt >/dev/null
fi

if [[ -x .venv/bin/python ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

# 6-digit STAN and 12-digit RRN to match ISO field formats.
STAN="$(date +%s | tail -c 7)"
RRN="$(date +%s%N | tail -c 13)"

log "Sending ISO transaction via switch (STAN=$STAN, RRN=$RRN)"
SIM_OUTPUT="$($PYTHON_BIN python_tests/single_iso_simulator.py \
  --profile pos \
  --field 2=1234567890123456 \
  --field 4=000000999999 \
  --field 41=POS-E2E1 \
  --field 11="$STAN" \
  --field 37="$RRN")"
printf '%s\n' "$SIM_OUTPUT"

if ! printf '%s' "$SIM_OUTPUT" | grep -q "Switch response"; then
  echo "ISO simulator did not return a switch response" >&2
  exit 1
fi

log "Checking switch persisted REQUEST and FRAUD_* events"
EVENTS_ROW_COUNT="$(docker exec -i jpos-postgresql psql -U postgres -d jpos -tAc "select count(*) from transaction_events where stan='${STAN}' and event_type in ('REQUEST','FRAUD_FLAG','FRAUD_DECLINE');")"
if [[ -z "$EVENTS_ROW_COUNT" || "$EVENTS_ROW_COUNT" -lt 2 ]]; then
  echo "Expected REQUEST + FRAUD event for STAN=${STAN}, got count=${EVENTS_ROW_COUNT}" >&2
  docker exec -i jpos-postgresql psql -U postgres -d jpos -c "select id, stan, rrn, event_type, rc, created_at from transaction_events where stan='${STAN}' order by created_at;"
  exit 1
fi

log "Checking backend fraud alerts endpoint"
ALERTS_JSON="$(curl -fsS "http://localhost:8000/fraud/alerts?limit=200")"
if ! printf '%s' "$ALERTS_JSON" | grep -q '"stan":"'"$STAN"'"'; then
  echo "Backend /fraud/alerts does not include STAN=${STAN}" >&2
  exit 1
fi

log "Checking backend flagged transactions endpoint"
FLAGGED_JSON="$(curl -fsS "http://localhost:8000/fraud/flagged-transactions?limit=200")"
if ! printf '%s' "$FLAGGED_JSON" | grep -q '"stan":"'"$STAN"'"'; then
  echo "Backend /fraud/flagged-transactions does not include STAN=${STAN}" >&2
  exit 1
fi

log "Checking frontend is serving"
if ! curl -fsS http://localhost:5173 >/dev/null; then
  echo "Frontend is not reachable on port 5173" >&2
  exit 1
fi

log "Automated E2E passed: ATM/POS -> Switch(Java/jPOS Fraud Engine) -> DB -> Backend API -> Frontend"
