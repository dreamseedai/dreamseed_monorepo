#!/usr/bin/env bash
# Deployment script for admin_front Next.js app
# This script builds and deploys the admin frontend to production
# Usage: ./deploy_admin_front.sh

set -euo pipefail

echo "================================================"
echo "🚀 DreamSeed Admin Frontend Deployment"
echo "================================================"

# Configuration
APP_DIR="/home/won/projects/dreamseed_monorepo/admin_front"
SERVICE_NAME="admin-front"
NGINX_TEST=true    # Set to false to skip nginx test/reload
HEALTH_CHECK_URL="https://admin.dreamseedai.com/questions"

echo "📁 1) Changing to project directory..."
cd "$APP_DIR"

echo "📥 2) Pulling latest code (git pull)..."
git pull --ff-only || {
    echo "⚠️  WARNING: git pull failed (might be local changes or not on a branch)"
    echo "    Continuing anyway..."
}

echo "📦 3) Installing dependencies (npm install)..."
npm install

echo "🏗️  4) Building Next.js application (npm run build)..."
NODE_ENV=production npm run build

echo "🔄 5) Restarting Next.js server..."
# Kill existing process
pkill -f "next-server" || echo "   No existing process found"
sleep 2

# Start new process
echo "   Starting Next.js on port 3100..."
PORT=3100 npm run start > /tmp/admin_front_prod.log 2>&1 &
NEXT_PID=$!
echo "   Started with PID: $NEXT_PID"

# Wait a bit for server to start
sleep 5

# Check if process is still running
if ps -p $NEXT_PID > /dev/null; then
    echo "   ✅ Next.js server started successfully"
else
    echo "   ❌ ERROR: Next.js server failed to start"
    echo "   Last 20 lines of log:"
    tail -20 /tmp/admin_front_prod.log
    exit 1
fi

if [ "$NGINX_TEST" = true ]; then
    echo "🧪 6) Testing NGINX config..."
    sudo nginx -t
    
    echo "🔄 7) Reloading NGINX..."
    sudo systemctl reload nginx
fi

echo "✅ 8) Health check..."
sleep 2
if curl -sSf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
    echo "   ✅ Health check passed: $HEALTH_CHECK_URL"
else
    echo "   ⚠️  WARNING: Health check failed for $HEALTH_CHECK_URL"
    echo "   Server might still be starting up..."
fi

echo ""
echo "================================================"
echo "🎉 Deployment finished successfully!"
echo "================================================"
echo ""
echo "Service Status:"
echo "  - Next.js PID: $NEXT_PID"
echo "  - Port: 3100"
echo "  - URL: https://admin.dreamseedai.com"
echo "  - Logs: tail -f /tmp/admin_front_prod.log"
echo ""
echo "Verify deployment:"
echo "  curl -I https://admin.dreamseedai.com/questions"
echo "  curl https://admin.dreamseedai.com/api/admin/questions/13164 | jq .id"
echo ""
echo "================================================"
