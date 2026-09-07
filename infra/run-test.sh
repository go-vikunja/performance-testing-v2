#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash hcloud openssh gettext openssl curl python3 coreutils git git-lfs
# Runs one headless locust test, then archives locust csv/html + rendered Grafana panels.
#   ./run-test.sh NAME [-u USERS] [-r SPAWN_RATE] [-t DURATION] [-c "Worker Glancer IntegrationBot"] [-e "WEIGHT_BOT=2 ..."]
# Results: runs/YYYY-MM-DD_HH-MM-SS-NAME/  (locust-report.html, locust_*.csv, grafana/*.png, meta.txt)
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh; source "$ENV_FILE"
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

name=${1:?name}; shift
users=500; rate=10; duration=10m; classes="Worker Glancer IntegrationBot"; envs=""
while getopts "u:r:t:c:e:" o; do case $o in
  u) users=$OPTARG;; r) rate=$OPTARG;; t) duration=$OPTARG;; c) classes=$OPTARG;; e) envs=$OPTARG;; esac; done

run_id=$(date +%Y-%m-%d_%H-%M-%S)
echo "==> syncing locust/ to loadgen"
scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ../locust/. "root@$LOADGEN_IP:/opt/perf/locust/"
$SSH "root@$LOADGEN_IP" 'cd /opt/perf/locust && docker build -q -t perf-locust . >/dev/null'
# Every run starts from the seeded state: drop the database and copy it back from the template reset.sh made.
if $SSH "root@$DB_IP" 'docker exec perf-postgres-1 psql -U vikunja -d postgres -Atc "select 1 from pg_database where datname = '"'"'vikunja_snap'"'"'"' | grep -q 1; then
  echo "==> restoring the seeded database from vikunja_snap"
  $SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose stop vikunja'
  $SSH "root@$DB_IP" 'docker exec perf-postgres-1 psql -U vikunja -d postgres -qc "drop database vikunja with (force)" -c "create database vikunja template vikunja_snap" >/dev/null'
  $SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose up -d vikunja'
  until $SSH "root@$VIKUNJA_IP" "curl -sf http://$VIKUNJA_PIP:3456/api/v2/info >/dev/null"; do sleep 2; done
else
  echo "==> no vikunja_snap database, running against the current state (run reset.sh to seed + snapshot)"
fi
echo "==> resetting postgres statistics"
$SSH "root@$DB_IP" 'docker exec perf-postgres-1 psql -U vikunja -qc "select pg_stat_statements_reset(); select pg_stat_reset();" >/dev/null'

echo "==> running $name: $users users, spawn $rate/s, $duration, classes: $classes"
$SSH "root@$LOADGEN_IP" "cd /opt/perf/locust && env $envs ./run.sh headless '$name' -u $users -r $rate -t $duration $classes"

exec ./collect-run.sh "$name" "$run_id" "$users" "$rate" "$duration" "$classes" "$envs"
