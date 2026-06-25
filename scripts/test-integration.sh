#!/usr/bin/env bash
#
# Real-database integration verification for sql2json.
#
# Provisions the docker-compose PostgreSQL and MySQL services, waits for them to
# become healthy, runs the `integration`-marked pytest suite against them, then
# tears the services down. This is the "clear command for real DB verification"
# that is separate from the fast, Docker-free unit suite (`uv run pytest`).
#
# Usage:
#   ./scripts/test-integration.sh            # provision, test, tear down
#   KEEP=1 ./scripts/test-integration.sh     # leave services running afterwards
#
# Requires Docker (or a `docker compose` shim such as podman-compose) and uv.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

services=(postgres mysql)

teardown() {
  if [[ "${KEEP:-0}" == "1" ]]; then
    echo ">> KEEP=1 set; leaving services running. Tear down with: docker compose down"
    return
  fi
  echo ">> Tearing down docker compose services..."
  docker compose down --volumes --remove-orphans || true
}
trap teardown EXIT

echo ">> Starting services: ${services[*]}"
# `--wait` blocks until healthchecks pass (docker compose v2). Fall back to a
# manual readiness poll for shims that don't support it.
if ! docker compose up -d --wait "${services[@]}" 2>/dev/null; then
  echo ">> '--wait' unsupported; starting without it and polling for readiness."
  docker compose up -d "${services[@]}"

  echo ">> Waiting for PostgreSQL..."
  for _ in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -U demo >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  echo ">> Waiting for MySQL..."
  for _ in $(seq 1 30); do
    if docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 --silent >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

echo ">> Running integration tests..."
# Point the suite at the compose services. With these overrides set the
# integration fixtures reuse the already-seeded compose stack instead of
# starting their own ephemeral testcontainers (the default when unset).
export SQL2JSON_TEST_PG_URL="postgresql+psycopg2://demo:demo@127.0.0.1:5432/demo"
export SQL2JSON_TEST_MYSQL_URL="mysql+pymysql://demo:demo@127.0.0.1:3306/demo"
# `dev` provides pytest; `integration` provides the psycopg2 / pymysql drivers.
uv run --extra dev --extra integration pytest -m integration tests/integration "$@"
