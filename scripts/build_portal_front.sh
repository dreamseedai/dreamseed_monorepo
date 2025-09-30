#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../portal_front"

# lockfile 없으면 먼저 생성 (npm ci 안전화)
[ -f package-lock.json ] || npm install --package-lock-only

# npm ci가 실패하면 npm install로 폴백 (초기 스캐폴드 환경 대비)
npm ci || npm install

npm run build

TS=$(date +%F_%H%M%S)
tar -czf "/tmp/portal_front_dist_${TS}.tgz" -C dist .
echo "/tmp/portal_front_dist_${TS}.tgz"


