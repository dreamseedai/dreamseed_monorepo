#!/usr/bin/env bash
set -euo pipefail

INSTANCE_NAME=${1:?instance name}
echo "🚀 Starting alert-threader@$INSTANCE_NAME..."
sudo systemctl start "alert-threader@$INSTANCE_NAME"
sudo systemctl status "alert-threader@$INSTANCE_NAME" --no-pager
echo "✅ Started alert-threader@$INSTANCE_NAME."