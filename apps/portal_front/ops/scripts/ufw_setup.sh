#!/usr/bin/env bash
set -euo pipefail

PORT=${1:-8080}

echo "🔥 Setting up UFW firewall for port ${PORT}"

# Allow SSH
ufw allow OpenSSH || true

# Allow specified port
ufw allow ${PORT}/tcp || true

# Enable UFW if not already enabled
ufw --force enable || true

echo "📊 Current UFW status:"
ufw status

echo "✅ UFW configured for port ${PORT}"
