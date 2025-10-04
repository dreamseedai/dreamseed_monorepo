#!/usr/bin/env bash
set -euo pipefail
PORT=${1:-8080}
ufw allow OpenSSH || true
ufw allow ${PORT}/tcp || true
ufw status


