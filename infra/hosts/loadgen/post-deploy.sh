#!/usr/bin/env bash
set -e
cd /opt/perf/locust
docker build -q -t perf-locust . >/dev/null
cat > .env <<ENV
VIKUNJA_PIP=${VIKUNJA_PIP}
MONITORING_PIP=${MONITORING_PIP}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
ENV
