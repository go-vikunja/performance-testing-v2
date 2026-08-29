#!/usr/bin/env bash
# Deletes everything setup.sh created. Keeps .env (secrets) unless --purge.
set -uo pipefail
cd "$(dirname "$0")"
source ./config.sh

for r in db vikunja monitoring loadgen; do hcloud server delete "$PREFIX-$r" 2>/dev/null & done
wait
hcloud firewall delete "$PREFIX-fw-base" 2>/dev/null
hcloud firewall delete "$PREFIX-fw-grafana" 2>/dev/null
hcloud network delete "$PREFIX-net" 2>/dev/null
hcloud ssh-key delete "$PREFIX-key" 2>/dev/null
[ "${1:-}" = --purge ] && rm -f "$ENV_FILE"
echo "torn down"
