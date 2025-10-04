#!/usr/bin/env bash
set -euo pipefail
PORT=${1:-8080}
DIR=${2:-$(pwd)}
echo "🔓 Opening UFW for $PORT/tcp (if enabled)"
ufw allow "$PORT"/tcp >/dev/null 2>&1 || true
ufw reload >/dev/null 2>&1 || true

HOST_IP=$(hostname -I | awk '{print $1}')
echo "🔎 Reachability pre‑check: http://$HOST_IP:$PORT"
if ! timeout 2 bash -lc "</dev/tcp/$HOST_IP/$PORT" 2>/dev/null; then
  echo "ℹ️  Starting server first; external check will follow."
fi

python3 -m http.server "$PORT" --directory "$DIR" --bind 0.0.0.0 &
PID=$!
sleep 1

if curl -sI "http://$HOST_IP:$PORT" | head -n1; then
  echo "✅ Server reachable at: http://$HOST_IP:$PORT"
else
  echo "⚠️  Not reachable externally. Check UFW, bind address, or host firewall."
fi

echo "💡 Windows quick test: ping $HOST_IP  →  curl http://$HOST_IP:$PORT  →  browser"
wait $PID


