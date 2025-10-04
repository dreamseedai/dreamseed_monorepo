#!/usr/bin/env bash
set -euo pipefail

INSTANCE_NAME=${1:?instance name}
echo "🛑 Stopping alert-threader@$INSTANCE_NAME..."
sudo systemctl stop "alert-threader@$INSTANCE_NAME"
sudo systemctl status "alert-threader@$INSTANCE_NAME" --no-pager
echo "✅ Stopped alert-threader@$INSTANCE_NAME."