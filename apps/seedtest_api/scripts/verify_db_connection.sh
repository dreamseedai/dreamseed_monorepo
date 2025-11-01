#!/bin/bash
# 데이터베이스 연결 및 스키마 상태 확인 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== 데이터베이스 연결 테스트 ==="
echo ""

# DATABASE_URL 확인
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}DATABASE_URL 환경 변수가 설정되지 않았습니다.${NC}"
    echo ""
    echo "예시 설정:"
    echo "  export DATABASE_URL='postgresql+psycopg://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed'"
    echo ""
    echo "또는 psql 직접 연결:"
    echo "  PGPASSWORD='DreamSeedAi@0908' psql -h 127.0.0.1 -p 5432 -U postgres -d dreamseed"
    echo ""
    exit 1
fi

# psql 연결 테스트
echo "1. PostgreSQL 연결 테스트..."
if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 연결 성공${NC}"
    psql "$DATABASE_URL" -c "SELECT version();" | head -3
else
    echo -e "${RED}❌ 연결 실패${NC}"
    echo ""
    echo "연결 정보 확인:"
    echo "  - 호스트: 127.0.0.1"
    echo "  - 포트: 5432"
    echo "  - 데이터베이스: dreamseed"
    echo "  - 사용자: postgres 또는 dreamseed"
    echo "  - 비밀번호: DreamSeedAi@0908"
    echo ""
    echo "URL 인코딩 필요: @ → %40"
    echo ""
    exit 1
fi

echo ""
echo "2. Core Domain 테이블 존재 확인..."
echo ""

TABLES=("question" "classroom" "session" "interest_goal" "features_topic_daily" "exam_results")

for table in "${TABLES[@]}"; do
    if psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" | grep -q "t"; then
        echo -e "${GREEN}✅ $table${NC}"
    else
        echo -e "${RED}❌ $table (존재하지 않음)${NC}"
    fi
done

echo ""
echo "3. attempt VIEW 확인..."
if psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'attempt');" | grep -q "t"; then
    echo -e "${GREEN}✅ attempt VIEW${NC}"
else
    echo -e "${RED}❌ attempt VIEW (존재하지 않음)${NC}"
fi

echo ""
echo "4. Alembic 마이그레이션 상태 확인..."
cd "$(dirname "$0")/../.." || exit
if [ -f ".venv/bin/alembic" ]; then
    echo "현재 리비전:"
    .venv/bin/alembic current 2>&1 | head -5 || echo "마이그레이션 상태 확인 불가"
    echo ""
    echo "최신 리비전:"
    .venv/bin/alembic heads 2>&1 | head -5
else
    echo -e "${YELLOW}⚠️  Alembic를 찾을 수 없습니다. 가상환경을 활성화하세요.${NC}"
fi

echo ""
echo "=== 검증 완료 ==="

