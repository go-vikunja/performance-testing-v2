# Tunables for setup.sh / teardown.sh. Override via env, e.g. LOCATION=fsn1 ./setup.sh

PREFIX="${PREFIX:-perf}"
LOCATION="${LOCATION:-nbg1}"
IMAGE="${IMAGE:-debian-13}"

# ccx = dedicated vCPU, cx = shared
TYPE_DB="${TYPE_DB:-ccx23}"
TYPE_VIKUNJA="${TYPE_VIKUNJA:-ccx23}"
TYPE_MONITORING="${TYPE_MONITORING:-cx23}"
TYPE_LOADGEN="${TYPE_LOADGEN:-cx33}"

NETWORK_CIDR="${NETWORK_CIDR:-10.0.0.0/16}"
SUBNET_CIDR="${SUBNET_CIDR:-10.0.1.0/24}"
NETWORK_ZONE="${NETWORK_ZONE:-eu-central}"

VIKUNJA_IMAGE="${VIKUNJA_IMAGE:-vikunja/vikunja:unstable}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:18}"

SSH_PUBKEY="${SSH_PUBKEY:-$HOME/.ssh/id_rsa.pub}"
# Only this IP may reach port 22. Default: current public IP.
ADMIN_IP="${ADMIN_IP:-$(curl -4 -s https://ifconfig.me)}"

# Generated secrets and discovered IPs land here
ENV_FILE="$(dirname "${BASH_SOURCE[0]}")/.env"
