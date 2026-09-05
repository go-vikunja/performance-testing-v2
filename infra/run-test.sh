#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash hcloud openssh gettext openssl curl python3 coreutils git git-lfs
# Runs one headless locust test, then archives locust csv/html + rendered Grafana panels.
#   ./run-test.sh NAME [-u USERS] [-r SPAWN_RATE] [-t DURATION] [-c "Worker Glancer IntegrationBot"] [-e "WEIGHT_BOT=2 ..."]
# Results: runs/NAME/YYYY-MM-DD_HH-MM-SS/  (locust-report.html, locust_*.csv, grafana/*.png, meta.txt)
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh; source "$ENV_FILE"
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

name=${1:?name}; shift
users=500; rate=10; duration=10m; classes="Worker Glancer IntegrationBot"; envs=""
while getopts "u:r:t:c:e:" o; do case $o in
  u) users=$OPTARG;; r) rate=$OPTARG;; t) duration=$OPTARG;; c) classes=$OPTARG;; e) envs=$OPTARG;; esac; done

run_id=$(date +%Y-%m-%d_%H-%M-%S)
out="../runs/$name/$run_id"; mkdir -p "$out/grafana"
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

echo "==> collecting locust results"
scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "root@$LOADGEN_IP:/opt/perf/locust/results/$name/." "$out/"
from=$(( $(cat "$out/start") * 1000 - 30000 )); to=$(( $(cat "$out/end") * 1000 + 30000 ))

echo "==> rendering grafana"
G="http://$MONITORING_IP:3000"; auth="admin:$GRAFANA_PASSWORD"
curl -sf -m 150 -u "$auth" "$G/render/d/perf-overview/perf-overview?from=$from&to=$to&kiosk&width=1600&height=3400&timeout=120" -o "$out/grafana/perf-overview.png"
curl -sf -u "$auth" "$G/api/dashboards/uid/perf-overview" | python3 -c '
import json,sys
for p in json.load(sys.stdin)["dashboard"]["panels"]:
    if p["type"]!="row": print(p["id"], p["title"].replace("/","-").replace(" ","_"))' | while read -r id title; do
  curl -sf -m 90 -u "$auth" "$G/render/d-solo/perf-overview/perf-overview?panelId=$id&from=$from&to=$to&width=1200&height=500&timeout=60" \
    -o "$out/grafana/$(printf %02d "$id")-$title.png" || echo "render failed: $title"
done
cat > "$out/meta.txt" <<META
run=$run_id name=$name users=$users spawn_rate=$rate duration=$duration classes="$classes" env="$envs"
vikunja_image=$VIKUNJA_IMAGE postgres_image=$POSTGRES_IMAGE types=$TYPE_VIKUNJA/$TYPE_DB
from=$from to=$to
grafana_url=$G/d/perf-overview/perf-overview?from=$from&to=$to
vikunja_version=$($SSH "root@$VIKUNJA_IP" "curl -s http://$VIKUNJA_PIP:3456/api/v2/info" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("version"))')
META
echo "==> collecting postgres top statements"
$SSH "root@$DB_IP" 'docker exec -i perf-postgres-1 psql -U vikunja -x' > "$out/pg-top-statements.txt" <<'SQL'
select round(total_exec_time) as total_ms, calls, round(mean_exec_time::numeric, 2) as mean_ms,
       round(total_plan_time) as plan_ms, round(mean_plan_time::numeric, 2) as mean_plan_ms, rows,
       shared_blks_hit, shared_blks_read, left(regexp_replace(query, '\s+', ' ', 'g'), 400) as query
from pg_stat_statements
where dbid = (select oid from pg_database where datname = current_database())
order by total_exec_time desc limit 30;
SQL
$SSH "root@$DB_IP" 'docker exec -i perf-postgres-1 psql -U vikunja' > "$out/pg-seq-scans.txt" <<'SQL'
select relname, seq_scan, seq_tup_read, idx_scan, n_tup_ins, n_tup_upd, n_tup_del
from pg_stat_user_tables order by seq_tup_read desc limit 20;
SQL
$SSH "root@$DB_IP" 'docker exec -i perf-postgres-1 psql -U vikunja' > "$out/pg-totals.txt" <<'SQL'
select sum(calls) as statements, round(sum(total_exec_time)) as total_exec_ms, round(sum(total_plan_time)) as total_plan_ms,
       round((sum(total_exec_time) / sum(calls))::numeric, 3) as avg_ms_per_statement,
       round((sum(total_plan_time) / sum(calls))::numeric, 3) as avg_plan_ms_per_statement
from pg_stat_statements
where dbid = (select oid from pg_database where datname = current_database());
select relname, indexrelname, idx_scan from pg_stat_user_indexes
where relname in (select relname from pg_stat_user_tables order by seq_tup_read desc limit 10)
order by relname, idx_scan desc;
SQL

python3 - "$out" <<'PY'
import csv, sys, os
out = sys.argv[1]
def rows(f):
    p = os.path.join(out, f)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
stats = rows("locust_stats.csv"); agg = next((r for r in stats if r["Name"] == "Aggregated"), {})
slow = sorted((r for r in stats if r["Name"] != "Aggregated"), key=lambda r: -float(r["Average Response Time"] or 0))[:10]
fails = rows("locust_failures.csv"); excs = rows("locust_exceptions.csv")
meta = open(os.path.join(out, "meta.txt")).read()
with open(os.path.join(out, "findings.md"), "w") as f:
    f.write(f"# Findings: {os.path.basename(os.path.dirname(out))} / {os.path.basename(out)}\n\n```\n{meta}```\n\n")
    f.write(f"## Locust summary\n\n- requests: {agg.get('Request Count')}  failures: {agg.get('Failure Count')}  rps: {agg.get('Requests/s')}\n")
    f.write(f"- response time ms: p50 {agg.get('50%')}  p95 {agg.get('95%')}  p99 {agg.get('99%')}  max {agg.get('Max Response Time')}\n")
    try:
        stm, ms, plan = [int(float(x)) for x in open(os.path.join(out, "pg-totals.txt")).read().split("\n")[2].split("|")[:3]]
        n = int(agg.get("Request Count") or 1)
        f.write(f"- postgres: {stm} statements = {stm / n:.1f} per request, {ms / n:.2f} ms DB exec + {plan / n:.2f} ms planning per request\n")
    except Exception as e:  # noqa: BLE001
        f.write(f"- postgres totals unavailable: {e}\n")
    f.write("\n")
    f.write("### Slowest endpoints (avg ms)\n\n| endpoint | reqs | avg | p50 | p95 |\n|---|---|---|---|---|\n")
    for r in slow:
        f.write(f"| {r['Type']} {r['Name']} | {r['Request Count']} | {float(r['Average Response Time']):.0f} | {r['50%']} | {r['95%']} |\n")
    f.write("\n### Failures\n\n")
    for r in fails: f.write(f"- {r['Occurrences']}x {r['Method']} {r['Name']}: {r['Error'][:120]}\n")
    for r in excs: f.write(f"- {r['Count']}x exception: {r['Message'][:120]}\n")
    if not fails and not excs: f.write("none\n")
    f.write("\n## Postgres\n\nSee `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.\n\n## Observations\n\n- \n")
PY

echo "==> committing run"
git -C .. add "runs/$name/$run_id"
git -C .. commit -qm "run: $name $run_id ($users users, $duration, $classes)" -- "runs/$name/$run_id"

echo "==> done: $out"; cat "$out/meta.txt"
