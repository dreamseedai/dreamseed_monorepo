#!/usr/bin/env bash
set -euo pipefail

INSTANCE_NAME=${1:?instance name}
echo "ℹ️  Status of alert-threader@$INSTANCE_NAME:"
sudo systemctl status "alert-threader@$INSTANCE_NAME" --no-pager