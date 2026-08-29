#!/usr/bin/env bash
# Runs on the loadgen VM. Usage:
#   ./run.sh seed [seed.py args]                      seed the instance, writes seed-state.json
#   ./run.sh ui [locust args] [UserClass ...]         web UI on :8089 (tunnel: ssh -L 8089:localhost:8089)
#   ./run.sh headless NAME -u 500 -r 10 -t 10m [...]  headless, results in results/NAME/
set -euo pipefail
cd "$(dirname "$0")"
source .env
HOST="http://${VIKUNJA_PIP}:3456"
IMG=perf-locust
RUN="docker run --rm --user 0 --network host -v $PWD:/mnt/locust -w /mnt/locust -e SEED_STATE=/mnt/locust/seed-state.json"
for v in ${!WEIGHT_@}; do RUN+=" -e $v"; done

case "${1:-}" in
  seed)
    shift
    $RUN -e PYTHONUNBUFFERED=1 --entrypoint python $IMG seed.py --host "$HOST" "$@"
    ;;
  ui)
    shift
    $RUN $IMG -f locustfile.py --host "$HOST" --web-host 127.0.0.1 "$@"
    ;;
  headless)
    shift; name=$1; shift
    # a previous run may still hold :8089
    for c in $(docker ps -q --filter ancestor=$IMG); do docker kill "$c" >/dev/null; done
    pkill -f "locust -f locustfile.py" 2>/dev/null || true
    for i in $(seq 1 30); do ss -ltn | grep -q ':8089 ' || break; sleep 1; done
    mkdir -p "results/$name"
    date +%s > "results/$name/start"
    # keep the web UI up so locust-exporter can scrape it during the run
    $RUN $IMG -f locustfile.py --host "$HOST" --autostart --autoquit 5 --web-host 127.0.0.1 \
      --csv "results/$name/locust" --csv-full-history --html "results/$name/locust-report.html" "$@"
    date +%s > "results/$name/end"
    ;;
  *) sed -n 2,5p "$0"; exit 1;;
esac
