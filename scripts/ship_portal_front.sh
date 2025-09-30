#!/usr/bin/env bash
set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-local}"

PKG="$(/home/won/projects/dreamseed_monorepo/scripts/build_portal_front.sh)"

if [[ "$DEPLOY_HOST" == "local" || "$DEPLOY_HOST" == "won@127.0.0.1" || "$DEPLOY_HOST" == "127.0.0.1" ]]; then
  sudo mkdir -p /srv/portal_front/releases
  sudo /usr/local/bin/deploy_portal_front.sh "$PKG"
else
  REM="/tmp/$(basename "$PKG")"
  scp "$PKG" "$DEPLOY_HOST:$REM"
  ssh "$DEPLOY_HOST" "sudo /usr/local/bin/deploy_portal_front.sh $REM"
fi


