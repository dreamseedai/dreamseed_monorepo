#!/usr/bin/env bash
set -euo pipefail

# =============================
# Alert Threader Instance Starter
# =============================

INSTANCE_NAME="${1:-default}"
INSTANCE_DIR="$(dirname "$0")"
PORT="${PORT:-9009}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# =============================
# Logging
# =============================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$INSTANCE_NAME] $*" >&2
}

log "Starting Alert Threader instance: $INSTANCE_NAME"
log "Working directory: $INSTANCE_DIR"
log "Port: $PORT, Host: $HOST"

# =============================
# Language Detection & Setup
# =============================
if [ -f "$INSTANCE_DIR/app.py" ]; then
    # Python FastAPI
    log "Detected Python FastAPI application"
    
    # Install dependencies
    log "Installing Python dependencies..."
    python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
    python3 -m pip install fastapi uvicorn httpx redis >/dev/null 2>&1 || true
    
    # Start application
    log "Starting Python FastAPI on $HOST:$PORT"
    exec uvicorn app:app \
        --host "$HOST" \
        --port "$PORT" \
        --proxy-headers \
        --forwarded-allow-ips='*' \
        --log-level "$LOG_LEVEL"
    
elif [ -f "$INSTANCE_DIR/index.js" ]; then
    # Node.js Express
    log "Detected Node.js Express application"
    
    # Setup package.json if missing
    if [ ! -f "$INSTANCE_DIR/package.json" ]; then
        log "Creating package.json..."
        cat > "$INSTANCE_DIR/package.json" << 'EOF'
{
  "name": "alert-threader-node",
  "version": "1.0.0",
  "type": "module",
  "description": "Alertmanager -> Slack Threader (Node.js)",
  "main": "index.js",
  "dependencies": {
    "express": "^4.18.2",
    "node-fetch": "^2.7.0",
    "redis": "^4.6.10"
  }
}
EOF
    fi
    
    # Install dependencies
    log "Installing Node.js dependencies..."
    cd "$INSTANCE_DIR"
    npm -s i express node-fetch@2 redis >/dev/null 2>&1 || true
    
    # Start application
    log "Starting Node.js Express on $HOST:$PORT"
    exec env PORT="$PORT" HOST="$HOST" node index.js
    
elif [ -f "$INSTANCE_DIR/main.go" ]; then
    # Go HTTP server
    log "Detected Go HTTP application"
    
    # Setup go.mod if missing
    if [ ! -f "$INSTANCE_DIR/go.mod" ]; then
        log "Creating go.mod..."
        cd "$INSTANCE_DIR"
        go mod init threader >/dev/null 2>&1 || true
    fi
    
    # Install dependencies and build
    log "Installing Go dependencies and building..."
    cd "$INSTANCE_DIR"
    go mod tidy >/dev/null 2>&1 || true
    go get github.com/redis/go-redis/v9@v9.5.1 >/dev/null 2>&1 || true
    go build -o threader . >/dev/null 2>&1 || true
    
    # Start application
    log "Starting Go HTTP server on $HOST:$PORT"
    exec env PORT="$PORT" HOST="$HOST" ./threader
    
else
    log "Error: No supported application file found in $INSTANCE_DIR"
    log "Expected: app.py (Python), index.js (Node.js), or main.go (Go)"
    log "Available files:"
    ls -la "$INSTANCE_DIR" >&2
    exit 1
fi
