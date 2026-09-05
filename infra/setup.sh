#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash hcloud openssh gettext openssl curl python3 coreutils
# Provisions db, vikunja, monitoring and loadgen servers on Hetzner Cloud.
# Idempotent: re-running reuses existing resources and re-applies compose files.
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

[ -f "$SSH_PUBKEY" ] || { echo "SSH_PUBKEY $SSH_PUBKEY not found"; exit 1; }

exists() { hcloud "$1" describe "$2" >/dev/null 2>&1; }
log() { echo "==> $*"; }
# `wait` without args always returns 0 and set -e ignores background jobs,
# so track pids and fail if any of them failed.
PIDS=()
# background jobs ignore SIGINT, so ctrl-c has to be forwarded as SIGTERM to the whole process group
trap 'trap - TERM; kill -TERM 0 2>/dev/null' INT TERM
wait_all() {
  local failed=0
  for pid in "${PIDS[@]}"; do wait "$pid" || failed=1; done
  PIDS=()
  [ "$failed" = 0 ] || { echo "a parallel step failed, aborting" >&2; exit 1; }
}

# --- secrets -------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<ENV
DB_PASSWORD=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -hex 8)
ENV
fi
source "$ENV_FILE"

# --- ssh key, network, firewalls ----------------------------------------
KEY="$PREFIX-key"
exists ssh-key "$KEY" || { log "ssh key"; hcloud ssh-key create --name "$KEY" --public-key-from-file "$SSH_PUBKEY" >/dev/null; }

NET="$PREFIX-net"
if ! exists network "$NET"; then
  log "network"
  hcloud network create --name "$NET" --ip-range "$NETWORK_CIDR" >/dev/null
  hcloud network add-subnet "$NET" --type cloud --network-zone "$NETWORK_ZONE" --ip-range "$SUBNET_CIDR" >/dev/null
fi

FW_BASE="$PREFIX-fw-base"
if ! exists firewall "$FW_BASE"; then
  log "firewall base (ssh from $ADMIN_IP only)"
  hcloud firewall create --name "$FW_BASE" >/dev/null
  hcloud firewall add-rule "$FW_BASE" --direction in --protocol tcp --port 22 --source-ips "$ADMIN_IP/32" >/dev/null
  hcloud firewall add-rule "$FW_BASE" --direction in --protocol icmp --source-ips "$ADMIN_IP/32" >/dev/null
  hcloud firewall apply-to-resource "$FW_BASE" --type label_selector --label-selector "$PREFIX=1" >/dev/null
fi
FW_GRAFANA="$PREFIX-fw-grafana"
if ! exists firewall "$FW_GRAFANA"; then
  log "firewall grafana (3000 public)"
  hcloud firewall create --name "$FW_GRAFANA" >/dev/null
  hcloud firewall add-rule "$FW_GRAFANA" --direction in --protocol tcp --port 3000 --source-ips 0.0.0.0/0 --source-ips ::/0 >/dev/null
  hcloud firewall apply-to-resource "$FW_GRAFANA" --type label_selector --label-selector "role=monitoring" >/dev/null
fi

# --- servers --------------------------------------------------------------
create_server() { # name type role
  local name="$PREFIX-$1"
  exists server "$name" && return
  log "server $name ($2)"
  hcloud server create --name "$name" --type "$2" --image "$IMAGE" --location "$LOCATION" \
    --ssh-key "$KEY" --network "$NET" --label "$PREFIX=1" --label "role=$3" \
    --user-data-from-file cloud-init/base.yaml >/dev/null &
  PIDS+=($!)
}
create_server db "$TYPE_DB" db
create_server vikunja "$TYPE_VIKUNJA" vikunja
create_server monitoring "$TYPE_MONITORING" monitoring
create_server loadgen "$TYPE_LOADGEN" loadgen
wait_all

ip_of()  { hcloud server ip "$PREFIX-$1"; }
pip_of() { hcloud server describe "$PREFIX-$1" -o json | python3 -c 'import json,sys;print(json.load(sys.stdin)["private_net"][0]["ip"])'; }
for r in db vikunja monitoring loadgen; do
  up=$(echo "$r" | tr a-z A-Z)
  ip=$(ip_of "$r"); pip=$(pip_of "$r")
  [ -n "$ip" ] && [ -n "$pip" ] || { echo "could not resolve IPs of $PREFIX-$r" >&2; exit 1; }
  eval "${up}_IP=$ip ${up}_PIP=$pip"
done
export DB_IP VIKUNJA_IP MONITORING_IP LOADGEN_IP DB_PIP VIKUNJA_PIP MONITORING_PIP LOADGEN_PIP
export DB_PASSWORD JWT_SECRET GRAFANA_PASSWORD VIKUNJA_IMAGE POSTGRES_IMAGE
# keep discovered IPs for locust/run.sh & friends
grep -vE '_P?IP=' "$ENV_FILE" > "$ENV_FILE.tmp"; mv "$ENV_FILE.tmp" "$ENV_FILE"
for v in DB_IP VIKUNJA_IP MONITORING_IP LOADGEN_IP DB_PIP VIKUNJA_PIP MONITORING_PIP LOADGEN_PIP; do echo "$v=${!v}" >> "$ENV_FILE"; done

SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
wait_ready() { # ip
  log "waiting for cloud-init on $1"
  for i in $(seq 1 60); do
    $SSH "root@$1" 'cloud-init status --wait >/dev/null 2>&1; test -x /usr/bin/docker' 2>/dev/null && return
    sleep 5
  done
  echo "host $1 never became ready" >&2; exit 1
}
deploy() { # role ip
  local role=$1 ip=$2 tmp; tmp=$(mktemp -d)
  wait_ready "$ip"
  log "deploying $role to $ip"
  cp -r "hosts/$role/." "$tmp/"
  # Substitute only our own variables so compose ${...} references survive
  find "$tmp" -type f -exec sh -c 'envsubst "$1" < "$2" > "$2.n" && mv "$2.n" "$2"' _ \
    '$DB_IP $VIKUNJA_IP $MONITORING_IP $LOADGEN_IP $DB_PIP $VIKUNJA_PIP $MONITORING_PIP $LOADGEN_PIP $DB_PASSWORD $JWT_SECRET $GRAFANA_PASSWORD $VIKUNJA_IMAGE $POSTGRES_IMAGE' {} \;
  $SSH "root@$ip" 'mkdir -p /opt/perf'
  scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "$tmp/." "root@$ip:/opt/perf/"
  [ "$role" = loadgen ] && scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ../locust "root@$ip:/opt/perf/"
  $SSH "root@$ip" 'cd /opt/perf && [ -f post-deploy.sh ] && bash post-deploy.sh; docker compose up -d --remove-orphans --pull always --force-recreate'
  rm -rf "$tmp"
}
deploy db "$DB_IP"
deploy vikunja "$VIKUNJA_IP"
deploy monitoring "$MONITORING_IP" & PIDS+=($!)
deploy loadgen "$LOADGEN_IP" & PIDS+=($!)
wait_all

log "waiting for vikunja to answer"
for i in $(seq 1 40); do
  $SSH "root@$VIKUNJA_IP" "curl -sf http://$VIKUNJA_PIP:3456/api/v2/info >/dev/null" && break
  if [ "$i" = 40 ]; then
    echo "vikunja did not come up; last logs:" >&2
    $SSH "root@$VIKUNJA_IP" 'cd /opt/perf && docker compose ps && docker compose logs --tail 30 vikunja' >&2
    exit 1
  fi
  sleep 3
done

cat <<OUT

Done.
  grafana     http://$MONITORING_IP:3000  (admin / $GRAFANA_PASSWORD)
  vikunja     http://$VIKUNJA_PIP:3456   (private only; ssh -L 3456:$VIKUNJA_PIP:3456 root@$LOADGEN_IP)
  locust ui   ssh -L 8089:localhost:8089 root@$LOADGEN_IP  then http://localhost:8089
  seed+run    ssh root@$LOADGEN_IP  'cd /opt/perf/locust && ./run.sh seed'  /  './run.sh'
OUT
