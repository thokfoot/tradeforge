#!/usr/bin/env bash
# trade-forge VPS deployment script
# Run this on your Ubuntu/Debian VPS. Sudo required.
# Usage: bash scripts/deploy.sh [--setup] [--ssl DOMAIN]

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="update"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup) MODE="setup"; shift ;;
    --ssl)   MODE="ssl"; DOMAIN="$2"; shift 2 ;;
    *)       echo "Usage: $0 [--setup] [--ssl DOMAIN]"; exit 1 ;;
  esac
done

if [[ "$MODE" == "setup" ]]; then
  echo "=== trade-forge: initial VPS setup ==="

  if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | bash
    sudo usermod -aG docker "$USER"
    echo "Docker installed. Log out and back in, then re-run: bash scripts/deploy.sh --setup"
    exit 0
  fi

  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo ""
    echo "Created .env from .env.example."
    echo "Edit .env now and set at least:"
    echo "  - GEMINI_API_KEY (paste your Gemini key)"
    echo "  - ENVIRONMENT=production"
    echo "  - ALERTS_ENABLED=1"
    echo "  - NEXT_PUBLIC_API_URL=  (empty/remove — nginx proxies /api for you)"
    echo ""
    read -rp "Press Enter after editing .env..."
  fi

  echo "Starting services..."
  docker compose up --build -d
  echo ""
  echo "App running on http://$(hostname -I | awk '{print $1}'):80"
  echo ""
  echo "Next: bash scripts/deploy.sh --ssl yourdomain.com"
  exit 0
fi

if [[ "$MODE" == "ssl" ]]; then
  if [[ -z "${DOMAIN:-}" ]]; then
    echo "Usage: $0 --ssl yourdomain.com"
    exit 1
  fi

  echo "=== Setting up HTTPS for $DOMAIN ==="

  if ! command -v certbot &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot
  fi

  # Stop nginx briefly so certbot can bind port 80
  docker compose stop nginx 2>/dev/null || true

  sudo certbot certonly --standalone -d "$DOMAIN" --agree-tos --non-interactive --email "admin@$DOMAIN"

  # Swap nginx config to SSL version
  sed "s/\$SERVER_DOMAIN/$DOMAIN/g" nginx/nginx-ssl.conf > nginx/nginx-ssl-runtime.conf

  # Point compose at the SSL-ready config
  export NGINX_CONF=nginx-ssl-runtime.conf
  docker compose up --build -d

  echo ""
  echo "HTTPS enabled: https://$DOMAIN"
  echo ""
  echo "Auto-renewal cron (add manually if needed):"
  echo "0 3 * * * certbot renew --quiet --pre-hook 'docker compose stop nginx' --post-hook 'docker compose up -d nginx'"
  exit 0
fi

# Default: update
echo "=== trade-forge: update ==="
git pull
docker compose up --build -d
echo "Updated and running."
docker compose ps
