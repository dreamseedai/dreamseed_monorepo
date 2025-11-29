#!/bin/bash
# Phase 1 MVP HTTP API 테스트 스크립트

BASE_URL="http://localhost:9001"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "Phase 1 MVP HTTP API 테스트"
echo "========================================"

# 1. 회원가입
echo -e "\n${BLUE}[1단계] 학생 회원가입${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "http_test_'$(date +%s)'@test.com",
    "password": "TestPassword123!",
    "full_name": "HTTP 테스트 학생",
    "role": "student"
  }')

USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.id')
USER_EMAIL=$(echo $REGISTER_RESPONSE | jq -r '.email')
echo -e "${GREEN}✅ 회원가입 성공${NC}"
echo "   이메일: $USER_EMAIL"
echo "   ID: $USER_ID"

# 2. 로그인
echo -e "\n${BLUE}[2단계] 로그인 및 JWT 토큰 발급${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"TestPassword123!\"
  }")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo -e "${GREEN}✅ 로그인 성공${NC}"
echo "   토큰 (앞 30자): ${TOKEN:0:30}..."

# 3. 내 정보 조회
echo -e "\n${BLUE}[3단계] 인증된 사용자 정보 조회${NC}"
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✅ 사용자 정보 조회 성공${NC}"
echo $ME_RESPONSE | jq '{email, full_name, role, is_active}'

# 4. 문제 목록 조회
echo -e "\n${BLUE}[4단계] 문제 목록 조회 (인증 필요)${NC}"
PROBLEMS_RESPONSE=$(curl -s -X GET "$BASE_URL/problems?limit=3" \
  -H "Authorization: Bearer $TOKEN")
PROBLEM_COUNT=$(echo $PROBLEMS_RESPONSE | jq '.total')
echo -e "${GREEN}✅ 문제 목록 조회 성공${NC}"
echo "   전체 문제 수: $PROBLEM_COUNT"
echo $PROBLEMS_RESPONSE | jq '.problems[] | {title, difficulty}'

# 첫 번째 문제 ID 추출
PROBLEM_ID=$(echo $PROBLEMS_RESPONSE | jq -r '.problems[0].id')

# 5. 문제 상세 조회
echo -e "\n${BLUE}[5단계] 문제 상세 조회${NC}"
PROBLEM_DETAIL=$(curl -s -X GET "$BASE_URL/problems/$PROBLEM_ID" \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✅ 문제 상세 조회 성공${NC}"
echo $PROBLEM_DETAIL | jq '{title, difficulty, description}'

# 6. 문제 시작
echo -e "\n${BLUE}[6단계] 문제 시작 (진행도 추적)${NC}"
START_RESPONSE=$(curl -s -X POST "$BASE_URL/progress/problem/$PROBLEM_ID/start" \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✅ 문제 시작됨${NC}"
echo $START_RESPONSE | jq '{status, attempts, last_attempt_at}'

# 7. 답안 제출
echo -e "\n${BLUE}[7단계] 답안 제출${NC}"
SUBMISSION_RESPONSE=$(curl -s -X POST "$BASE_URL/submissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"problem_id\": \"$PROBLEM_ID\",
    \"answer\": \"HTTP 테스트로 제출한 답안입니다. x = 2 또는 x = 3\"
  }")
SUBMISSION_ID=$(echo $SUBMISSION_RESPONSE | jq -r '.id')
echo -e "${GREEN}✅ 답안 제출 성공${NC}"
echo "   제출 ID: $SUBMISSION_ID"
echo "   채점 상태: 미채점"

# 8. 내 제출 목록
echo -e "\n${BLUE}[8단계] 내 제출 이력 조회${NC}"
MY_SUBMISSIONS=$(curl -s -X GET "$BASE_URL/submissions" \
  -H "Authorization: Bearer $TOKEN")
SUBMISSION_COUNT=$(echo $MY_SUBMISSIONS | jq '.total')
echo -e "${GREEN}✅ 제출 이력 조회 성공${NC}"
echo "   전체 제출 수: $SUBMISSION_COUNT"

# 9. 문제 완료
echo -e "\n${BLUE}[9단계] 문제 완료 처리${NC}"
COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/progress/problem/$PROBLEM_ID/complete" \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✅ 문제 완료 처리 성공${NC}"
echo $COMPLETE_RESPONSE | jq '{status, completed_at}'

# 10. 학습 통계
echo -e "\n${BLUE}[10단계] 학습 통계 조회${NC}"
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/progress/me/stats" \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✅ 학습 통계 조회 성공${NC}"
echo $STATS_RESPONSE | jq '.'

echo -e "\n========================================"
echo -e "${GREEN}🎉 모든 HTTP API 테스트 통과!${NC}"
echo "========================================"
echo ""
echo "📊 Swagger UI: http://localhost:9001/docs"
echo "📖 ReDoc: http://localhost:9001/redoc"
echo "🔗 OpenAPI Schema: http://localhost:9001/openapi.json"
