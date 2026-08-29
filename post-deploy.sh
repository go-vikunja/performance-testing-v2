#!/usr/bin/env bash
# Pull community dashboards; pin datasource to our provisioned uid.
set -e
cd /opt/perf/grafana/dashboards
for id in 1860 9628 14282; do
  [ -f "gnet-$id.json" ] && continue
  curl -sf "https://grafana.com/api/dashboards/$id/revisions/latest/download" \
    | sed 's/${DS_PROMETHEUS}/prometheus/g; s/${DS__VICTORIAMETRICS}/prometheus/g' > "gnet-$id.json"
done
