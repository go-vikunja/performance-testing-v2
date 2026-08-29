#!/usr/bin/env bash
# Runs one headless locust test, then archives locust csv/html + rendered Grafana panels.
#   ./run-test.sh NAME [-u USERS] [-r SPAWN_RATE] [-t DURATION] [-c "Worker Glancer IntegrationBot"] [-e "WEIGHT_BOT=2 ..."]
# Results: results/NAME/  (locust-report.html, locust_*.csv, grafana/*.png)
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh; source "$ENV_FILE"
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

name=${1:?name}; shift
users=500; rate=10; duration=10m; classes="Worker Glancer IntegrationBot"; envs=""
while getopts "u:r:t:c:e:" o; do case $o in
  u) users=$OPTARG;; r) rate=$OPTARG;; t) duration=$OPTARG;; c) classes=$OPTARG;; e) envs=$OPTARG;; esac; done

out="../results/$name"; mkdir -p "$out/grafana"
echo "==> running $name: $users users, spawn $rate/s, $duration, classes: $classes"
$SSH "root@$LOADGEN_IP" "cd /opt/perf/locust && env $envs ./run.sh headless '$name' -u $users -r $rate -t $duration $classes" | tail -40

echo "==> collecting locust results"
scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "root@$LOADGEN_IP:/opt/perf/locust/results/$name/." "$out/"
from=$(( $(cat "$out/start") * 1000 - 30000 )); to=$(( $(cat "$out/end") * 1000 + 30000 ))

echo "==> rendering grafana"
G="http://$MONITORING_IP:3000"; auth="admin:$GRAFANA_PASSWORD"
curl -sf -u "$auth" "$G/render/d/perf-overview/perf-overview?from=$from&to=$to&kiosk&width=1600&height=3400&timeout=120" -o "$out/grafana/perf-overview.png"
curl -sf -u "$auth" "$G/api/dashboards/uid/perf-overview" | python3 -c '
import json,sys
for p in json.load(sys.stdin)["dashboard"]["panels"]:
    if p["type"]!="row": print(p["id"], p["title"].replace("/","-").replace(" ","_"))' | while read -r id title; do
  curl -sf -u "$auth" "$G/render/d-solo/perf-overview/perf-overview?panelId=$id&from=$from&to=$to&width=1200&height=500&timeout=60" \
    -o "$out/grafana/$(printf %02d "$id")-$title.png" || echo "render failed: $title"
done
cat > "$out/meta.txt" <<META
name=$name users=$users spawn_rate=$rate duration=$duration classes="$classes" env="$envs"
vikunja_image=$VIKUNJA_IMAGE postgres_image=$POSTGRES_IMAGE types=$TYPE_VIKUNJA/$TYPE_DB
from=$from to=$to
grafana_url=$G/d/perf-overview/perf-overview?from=$from&to=$to
vikunja_version=$($SSH "root@$VIKUNJA_IP" "curl -s http://$VIKUNJA_PIP:3456/api/v2/info" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("version"))')
META
echo "==> done: $out"; cat "$out/meta.txt"
