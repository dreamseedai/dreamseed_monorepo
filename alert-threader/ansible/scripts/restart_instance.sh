#!/usr/bin/env bash
set -euo pipefail

INSTANCE_NAME=${1:?instance name}
echo "🔄 Restarting alert-threader@$INSTANCE_NAME..."
sudo systemctl restart "alert-threader@$INSTANCE_NAME"
sudo systemctl status "alert-threader@$INSTANCE_NAME" --no-pager
echo "✅ Restarted alert-threader@$INSTANCE_NAME."