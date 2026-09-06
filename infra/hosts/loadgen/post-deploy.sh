#!/usr/bin/env bash
set -e
cd /opt/perf/locust
docker build -q -t perf-locust . >/dev/null
cat > .env <<ENV
VIKUNJA_PIP=${VIKUNJA_PIP}
MONITORING_PIP=${MONITORING_PIP}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
ENV
# 3000 users cycle >24k sockets through TIME_WAIT; default range (32768-60999) runs out
cat > /etc/sysctl.d/90-loadgen.conf <<SYSCTL
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 8192
fs.file-max = 2097152
SYSCTL
sysctl -q --system
