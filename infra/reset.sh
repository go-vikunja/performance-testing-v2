#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash hcloud openssh gettext openssl curl python3 coreutils
# Wipes the database and reseeds, so every run starts from the same state.
#   ./reset.sh [seed.py args]     e.g. ./reset.sh --users 100 --tasks 500
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh; source "$ENV_FILE"
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

echo "==> stopping vikunja, recreating postgres volume"
$SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose stop vikunja'
$SSH "root@$DB_IP" 'cd /opt/perf && docker compose down -v && docker compose up -d'
$SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose up -d vikunja'
until $SSH "root@$VIKUNJA_IP" "curl -sf http://$VIKUNJA_PIP:3456/api/v2/info >/dev/null"; do sleep 2; done
echo "==> syncing locust/ to loadgen"
scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ../locust/. "root@$LOADGEN_IP:/opt/perf/locust/"
$SSH "root@$LOADGEN_IP" 'cd /opt/perf/locust && docker build -q -t perf-locust . >/dev/null'
echo "==> seeding"
$SSH "root@$LOADGEN_IP" "cd /opt/perf/locust && ./run.sh seed $*"
echo "==> snapshotting the seeded database (run-test.sh restores it before every run)"
$SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose stop vikunja'
$SSH "root@$DB_IP" 'docker exec perf-postgres-1 psql -U vikunja -d postgres -qc "drop database if exists vikunja_snap with (force)" -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '"'"'vikunja'"'"' and pid <> pg_backend_pid()" -c "create database vikunja_snap template vikunja" >/dev/null'
$SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose up -d vikunja'
until $SSH "root@$VIKUNJA_IP" "curl -sf http://$VIKUNJA_PIP:3456/api/v2/info >/dev/null"; do sleep 2; done
# pg_stat_statements accumulates since server start; start every run from zero
$SSH "root@$DB_IP" 'docker exec perf-postgres-1 psql -U vikunja -c "select pg_stat_statements_reset(); select pg_stat_reset();" >/dev/null'
