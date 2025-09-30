#!/usr/bin/env bash
set -e -o pipefail

API_DIR="/home/won/projects/dreamseed_monorepo/portal_api"
DB_USER="postgres"            # 필요 시 dreamseed 등으로 변경
DB_PASS="DreamSeedAi@0908"    # 현재 계획된 비밀번호
DB_HOST="127.0.0.1"
DB_PORT="5432"
DB_NAME="dreamseed"
EMAIL="you@example.com"
PASS="Test1234!"

cd "$API_DIR"
python -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip install -r requirements.txt

# DB 없으면 생성 (비번 인증 실패 시 여기서 멈춤)
export PGPASSWORD="$DB_PASS"
psql -h "$DB_HOST" -U "$DB_USER" -P pager=off -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || psql -h "$DB_HOST" -U "$DB_USER" -P pager=off -c "CREATE DATABASE ${DB_NAME};"

# 마이그레이션
alembic upgrade head
alembic current || true

# 서버 기동
export PYTHONPATH="$API_DIR"
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8012 --log-level warning &
PID=$!
sleep 1

# 헬스
curl -sf http://127.0.0.1:8012/__ok >/dev/null && echo "[OK] __ok"

# 회원가입(있으면 무시)
curl -s -X POST http://127.0.0.1:8012/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" >/dev/null || true

# 로그인 → AT 추출 (jq 없이 파이썬 사용)
AT=$(curl -s -X POST http://127.0.0.1:8012/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | python - <<'PY'
import sys, json
try:
    print(json.load(sys.stdin).get("access_token",""))
except Exception:
    print("")
PY
)

if [ -z "$AT" ]; then
  echo "Login failed (no access_token)"; kill $PID; exit 1
fi

# me 확인
curl -s http://127.0.0.1:8012/auth/me -H "Authorization: Bearer $AT" && echo

# 콘텐츠 생성 & 조회
curl -s -X POST http://127.0.0.1:8012/content/ \
  -H "Authorization: Bearer $AT" -H "Content-Type: application/json" \
  -d '{"title":"Demo","doc":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"hello"}]},{"type":"math","attrs":{"latex":"\\frac{a}{b}"}}]}}' && echo

curl -s http://127.0.0.1:8012/content/ -H "Authorization: Bearer $AT" && echo

# 종료
kill $PID
echo "[DONE] Smoke test complete."
