#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-}"
[ -n "$PORT" ] || { echo "usage: ufw-ensure-port <port>"; exit 1; }

echo "UFW 포트 $PORT 확인 중..."

# UFW 켜져 있지 않으면 켭니다(무해)
if sudo ufw status | grep -q inactive; then
    echo "UFW 활성화 중..."
    sudo ufw --force enable || true
fi

# 이미 허용되어 있는지 검사 후 없으면 추가
if ! sudo ufw status | grep -qE "\\b${PORT}/tcp\\b.*ALLOW"; then
    echo "UFW에 포트 $PORT 추가 중..."
    sudo ufw allow ${PORT}/tcp
    echo "포트 $PORT가 UFW에 추가되었습니다."
else
    echo "포트 $PORT는 이미 UFW에서 허용되어 있습니다."
fi

# 80/443도 서비스 단계에서 같이 열고 싶다면 주석 해제
# for p in 80 443; do
#   ufw status | grep -qE "\\b${p}/tcp\\b.*ALLOW" || ufw allow ${p}/tcp
# done

echo "UFW 상태:"
sudo ufw status | grep -E "\\b${PORT}/tcp\\b" || echo "포트 $PORT 규칙을 찾을 수 없습니다."
