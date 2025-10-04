#!/bin/bash

# 🧩 라우팅 품질 분석 (hint 집계)

set -e

LOG_FILE="/tmp/router.log"

echo "🧩 DreamSeed AI 라우팅 품질 분석"
echo "=================================="

if [ ! -f "$LOG_FILE" ]; then
  echo "❌ 로그 파일이 없습니다: $LOG_FILE"
  echo "💡 라우터를 실행하고 요청을 보내면 로그가 생성됩니다."
  exit 1
fi

# 로그 파일 크기 확인
LOG_SIZE=$(wc -l < "$LOG_FILE")
if [ $LOG_SIZE -eq 0 ]; then
  echo "❌ 로그가 비어있습니다."
  exit 1
fi

echo "📋 총 로그 라인 수: $LOG_SIZE"
echo ""

# 1) Hint별 분포
echo "1️⃣ Hint별 분포"
echo "-------------------"
echo "📊 Hint별 요청 수:"
awk '{print $8}' "$LOG_FILE" | sed 's/hint="//' | sed 's/"//' | sort | uniq -c | sort -nr | head -10

echo ""

# 2) 라우팅 품질 인사이트
echo "2️⃣ 라우팅 품질 인사이트"
echo "-------------------------"
FAST_LEN_COUNT=$(awk '$8 ~ /fast_len/' "$LOG_FILE" | wc -l)
FAST_KW_COUNT=$(awk '$8 ~ /fast_kw/' "$LOG_FILE" | wc -l)
CODE_KW_COUNT=$(awk '$8 ~ /code_kw/' "$LOG_FILE" | wc -l)
GENERAL_KW_COUNT=$(awk '$8 ~ /general_kw/' "$LOG_FILE" | wc -l)

echo "📊 라우팅 패턴 분석:"
echo "  - Fast 길이 기반: $FAST_LEN_COUNT회"
echo "  - Fast 키워드 기반: $FAST_KW_COUNT회"
echo "  - Code 키워드 기반: $CODE_KW_COUNT회"
echo "  - General 키워드 기반: $GENERAL_KW_COUNT회"

echo ""

# 3) 라우팅 품질 권장사항
echo "3️⃣ 라우팅 품질 권장사항"
echo "-------------------------"

# Fast 레인 분석
if [ $FAST_LEN_COUNT -gt $FAST_KW_COUNT ]; then
  echo "💡 Fast 레인은 주로 길이 기반으로 동작 중"
  echo "   → 키워드 기반 라우팅 강화 고려"
  echo "   → '짧게|핵심|한줄|요약' 키워드 추가"
else
  echo "✅ Fast 레인은 키워드 기반으로 잘 동작 중"
fi

# Code 레인 분석
if [ $CODE_KW_COUNT -lt $((LOG_SIZE / 20)) ]; then
  echo "💡 Code 레인 사용률 낮음 ($CODE_KW_COUNT회 < $((LOG_SIZE / 20))회)"
  echo "   → 코딩 키워드 확장 고려"
  echo "   → 'SELECT|테스트|리팩터|디버그|알고리즘' 키워드 추가"
else
  echo "✅ Code 레인 사용률 적절 ($CODE_KW_COUNT회)"
fi

# General 레인 분석
if [ $GENERAL_KW_COUNT -gt $((LOG_SIZE * 80 / 100)) ]; then
  echo "💡 General 레인 사용률이 높음 ($GENERAL_KW_COUNT회 > $((LOG_SIZE * 80 / 100))회)"
  echo "   → 라우팅 규칙 재검토 고려"
else
  echo "✅ General 레인 사용률 적절 ($GENERAL_KW_COUNT회)"
fi

echo ""

# 4) 길이별 분석
echo "4️⃣ 길이별 분석"
echo "-------------------"
echo "📊 프롬프트 길이 분포:"
awk '{print $8}' "$LOG_FILE" | sed 's/hint="//' | sed 's/"//' | sed 's/.*len=//' | sort -n | awk '
{
  if ($1 < 50) short++
  else if ($1 < 200) medium++
  else long++
}
END {
  printf "  - 짧은 프롬프트 (<50자): %d회\n", short+0
  printf "  - 중간 프롬프트 (50-200자): %d회\n", medium+0
  printf "  - 긴 프롬프트 (>200자): %d회\n", long+0
}'

echo ""

# 5) 성능별 분석
echo "5️⃣ 성능별 분석"
echo "-------------------"
echo "📊 레인별 평균 응답시간:"
for hint in "fast_len" "fast_kw" "code_kw" "general_kw"; do
  HINT_AVG=$(awk -v hint="$hint" '$8 ~ hint {print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
  HINT_COUNT=$(awk -v hint="$hint" '$8 ~ hint' "$LOG_FILE" | wc -l)
  echo "  - $hint: ${HINT_AVG}ms ($HINT_COUNT회)"
done

echo ""

# 6) 개선 제안
echo "6️⃣ 개선 제안"
echo "---------------"

# Fast 레인 개선
if [ $FAST_LEN_COUNT -gt $FAST_KW_COUNT ]; then
  echo "🔧 Fast 레인 개선:"
  echo "   sed -i 's/if re.search(r\"빠른|간단|요약\"/if re.search(r\"빠른|간단|요약|짧게|핵심|한줄\"/' router.py"
fi

# Code 레인 개선
if [ $CODE_KW_COUNT -lt $((LOG_SIZE / 20)) ]; then
  echo "🔧 Code 레인 개선:"
  echo "   sed -i 's/if re.search(r\"코드|프로그래밍|함수|클래스|import|def|class\"/if re.search(r\"코드|프로그래밍|함수|클래스|import|def|class|SELECT|테스트|리팩터|디버그|알고리즘\"/' router.py"
fi

echo ""
echo "🎯 라우팅 품질 분석 완료!"
echo "💡 개선 후: ./load-test-10.sh로 성능 검증"
