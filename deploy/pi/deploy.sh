#!/usr/bin/env bash
# ------------------------------------------------------------------
# deploy.sh — Deploy blackroad-stripe-service to Raspberry Pi(s)
#
# Usage:
#   ./deploy/pi/deploy.sh                   # deploy to all configured Pis
#   ./deploy/pi/deploy.sh lucidia.local     # deploy to specific host
# ------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults (overridable via env)
PI_USER="${PI_USER:-pi}"
DEPLOY_PATH="${PI_DEPLOY_PATH:-/opt/blackroad/stripe-service}"
SERVICE_NAME="blackroad-stripe"

# Target hosts: passed as args, or fall back to env vars
if [ $# -gt 0 ]; then
  HOSTS=("$@")
else
  HOSTS=()
  [ -n "${PI_HOST_1:-}" ] && HOSTS+=("$PI_HOST_1")
  [ -n "${PI_HOST_2:-}" ] && HOSTS+=("$PI_HOST_2")
fi

if [ ${#HOSTS[@]} -eq 0 ]; then
  echo "Error: No target hosts. Set PI_HOST_1/PI_HOST_2 or pass hosts as arguments."
  exit 1
fi

echo "=== BlackRoad Stripe Service — Pi Deploy ==="
echo "Targets: ${HOSTS[*]}"
echo "Deploy path: $DEPLOY_PATH"
echo ""

for HOST in "${HOSTS[@]}"; do
  echo "--- Deploying to $PI_USER@$HOST ---"

  # Ensure target directory exists
  ssh "$PI_USER@$HOST" "sudo mkdir -p $DEPLOY_PATH && sudo chown $PI_USER:$PI_USER $DEPLOY_PATH"

  # Sync project files (exclude dev artifacts)
  rsync -avz --delete \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='coverage' \
    "$PROJECT_DIR/" "$PI_USER@$HOST:$DEPLOY_PATH/"

  # Install production dependencies on the Pi
  ssh "$PI_USER@$HOST" "cd $DEPLOY_PATH && npm ci --omit=dev"

  # Copy systemd service file and reload
  ssh "$PI_USER@$HOST" "sudo cp $DEPLOY_PATH/deploy/pi/blackroad-stripe.service /etc/systemd/system/$SERVICE_NAME.service && sudo systemctl daemon-reload"

  # Copy nginx config if nginx is installed
  ssh "$PI_USER@$HOST" "
    if command -v nginx &>/dev/null; then
      sudo cp $DEPLOY_PATH/deploy/pi/nginx.conf /etc/nginx/sites-available/$SERVICE_NAME
      sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/$SERVICE_NAME
      sudo nginx -t && sudo systemctl reload nginx
    fi
  "

  # Restart the service
  ssh "$PI_USER@$HOST" "sudo systemctl enable $SERVICE_NAME && sudo systemctl restart $SERVICE_NAME"

  # Verify
  sleep 2
  ssh "$PI_USER@$HOST" "curl -sf http://localhost:3000/api/health" && echo " [OK] $HOST healthy" || echo " [WARN] $HOST health check failed"

  echo ""
done

echo "=== Deploy complete ==="
