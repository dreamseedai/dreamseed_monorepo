#!/usr/bin/env bash
set -euo pipefail

PORT=${1:-8080}
DIR=${2:-$(pwd)}

echo "🚀 Starting HTTP server on port ${PORT} for directory ${DIR}"
echo "🌐 Access via: http://$(hostname -I | awk '{print $1}'):${PORT}"
echo "📋 Safe ports: 80, 443, 8000, 8080, 3000, 5173"
echo "🚫 Blocked ports: 6000, 6665-6669, 10080"

python3 -m http.server "$PORT" --directory "$DIR" --bind 0.0.0.0
