#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash openssh gettext coreutils
# Re-applies hosts/<role>/ to one running host (config edits, image swaps) without re-running setup.sh.
#   ./redeploy.sh vikunja                      # compose up -d with the current hosts/vikunja
#   VIKUNJA_IMAGE=ghcr.io/go-vikunja/vikunja:pr-3721 ./redeploy.sh vikunja
#   ./redeploy.sh db --restart postgres        # postgresql.conf changes need a restart, not just up -d
set -euo pipefail
cd "$(dirname "$0")"
set -a; source ./config.sh; source "$ENV_FILE"; set +a  # envsubst runs in a child
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
role=${1:?role}; shift
restart=""
[ "${1:-}" = "--restart" ] && restart=$2
ip_var="$(echo "$role" | tr a-z A-Z)_IP"; ip=${!ip_var}
tmp=$(mktemp -d)
cp -r "hosts/$role/." "$tmp/"
find "$tmp" -type f -exec sh -c 'envsubst "$1" < "$2" > "$2.n" && mv "$2.n" "$2"' _ \
  '$DB_IP $VIKUNJA_IP $MONITORING_IP $LOADGEN_IP $DB_PIP $VIKUNJA_PIP $MONITORING_PIP $LOADGEN_PIP $DB_PASSWORD $JWT_SECRET $GRAFANA_PASSWORD $VIKUNJA_IMAGE $POSTGRES_IMAGE' {} \;
scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "$tmp/." "root@$ip:/opt/perf/"
rm -rf "$tmp"
$SSH "root@$ip" "cd /opt/perf && docker compose up -d --pull always ${restart:+&& docker compose restart $restart}"
if [ "$role" = vikunja ]; then
  until $SSH "root@$VIKUNJA_IP" "curl -sf http://$VIKUNJA_PIP:3456/api/v2/info" | python3 -c 'import json,sys;print("vikunja", json.load(sys.stdin)["version"])'; do sleep 2; done
fi
