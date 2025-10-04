#!/bin/bash

# 📸 주간 비교 (A/B 비교용 스냅샷)

set -e

echo "📸 DreamSeed AI 주간 비교"
echo "=========================="

# 현재 날짜
CURRENT_DATE=$(date +%Y-%m-%d)
WEEK_AGO_DATE=$(date -d '7 days ago' +%Y-%m-%d)

CURRENT_FILE="/tmp/6line-$CURRENT_DATE.txt"
WEEK_AGO_FILE="/tmp/6line-$WEEK_AGO_DATE.txt"

echo "📅 비교 기간: $WEEK_AGO_DATE → $CURRENT_DATE"
echo ""

# 파일 존재 확인
if [ ! -f "$CURRENT_FILE" ]; then
  echo "❌ 현재 스냅샷이 없습니다: $CURRENT_FILE"
  echo "💡 ./6line-summary.sh를 먼저 실행하세요."
  exit 1
fi

if [ ! -f "$WEEK_AGO_FILE" ]; then
  echo "❌ 1주 전 스냅샷이 없습니다: $WEEK_AGO_FILE"
  echo "💡 1주 후에 다시 실행하세요."
  exit 1
fi

echo "📊 주간 변화 분석"
echo "=================="

# 각 지표별 변화 분석
echo "1️⃣ P95 응답시간 변화"
echo "-------------------"
CURRENT_P95=$(grep "P95_latency_ms:" "$CURRENT_FILE" | cut -d' ' -f2)
WEEK_AGO_P95=$(grep "P95_latency_ms:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
P95_DELTA=$((CURRENT_P95 - WEEK_AGO_P95))

echo "  이번 주: ${CURRENT_P95}ms"
echo "  지난 주: ${WEEK_AGO_P95}ms"
echo "  변화: ${P95_DELTA}ms"

if [ $P95_DELTA -gt 50 ]; then
  echo "  🚨 P95가 크게 증가했습니다 (+${P95_DELTA}ms)"
  echo "     → --max-model-len 감소 고려"
elif [ $P95_DELTA -lt -50 ]; then
  echo "  ✅ P95가 크게 개선되었습니다 (${P95_DELTA}ms)"
else
  echo "  ✅ P95가 안정적입니다 (${P95_DELTA}ms)"
fi

echo ""

echo "2️⃣ 에러율 변화"
echo "-------------"
CURRENT_ERROR=$(grep "Error_rate_percent:" "$CURRENT_FILE" | cut -d' ' -f2)
WEEK_AGO_ERROR=$(grep "Error_rate_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
ERROR_DELTA=$((CURRENT_ERROR - WEEK_AGO_ERROR))

echo "  이번 주: ${CURRENT_ERROR}%"
echo "  지난 주: ${WEEK_AGO_ERROR}%"
echo "  변화: ${ERROR_DELTA}%"

if [ $ERROR_DELTA -gt 2 ]; then
  echo "  🚨 에러율이 증가했습니다 (+${ERROR_DELTA}%)"
  echo "     → 안정성 점검 필요"
elif [ $ERROR_DELTA -lt -2 ]; then
  echo "  ✅ 에러율이 개선되었습니다 (${ERROR_DELTA}%)"
else
  echo "  ✅ 에러율이 안정적입니다 (${ERROR_DELTA}%)"
fi

echo ""

echo "3️⃣ GPU VRAM 변화"
echo "----------------"
CURRENT_VRAM=$(grep "GPU_VRAM_max_percent:" "$CURRENT_FILE" | cut -d' ' -f2)
WEEK_AGO_VRAM=$(grep "GPU_VRAM_max_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
VRAM_DELTA=$((CURRENT_VRAM - WEEK_AGO_VRAM))

echo "  이번 주: ${CURRENT_VRAM}%"
echo "  지난 주: ${WEEK_AGO_VRAM}%"
echo "  변화: ${VRAM_DELTA}%"

if [ $VRAM_DELTA -gt 10 ]; then
  echo "  🚨 GPU VRAM 사용률이 증가했습니다 (+${VRAM_DELTA}%)"
  echo "     → 메모리 최적화 고려"
elif [ $VRAM_DELTA -lt -10 ]; then
  echo "  ✅ GPU VRAM 사용률이 개선되었습니다 (${VRAM_DELTA}%)"
else
  echo "  ✅ GPU VRAM 사용률이 안정적입니다 (${VRAM_DELTA}%)"
fi

echo ""

echo "4️⃣ Fast 레인 비율 변화"
echo "----------------------"
CURRENT_FAST=$(grep "Fast_lane_ratio_percent:" "$CURRENT_FILE" | cut -d' ' -f2)
WEEK_AGO_FAST=$(grep "Fast_lane_ratio_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
FAST_DELTA=$((CURRENT_FAST - WEEK_AGO_FAST))

echo "  이번 주: ${CURRENT_FAST}%"
echo "  지난 주: ${WEEK_AGO_FAST}%"
echo "  변화: ${FAST_DELTA}%"

if [ $FAST_DELTA -gt 5 ]; then
  echo "  ✅ Fast 레인 사용률이 증가했습니다 (+${FAST_DELTA}%)"
elif [ $FAST_DELTA -lt -5 ]; then
  echo "  💡 Fast 레인 사용률이 감소했습니다 (${FAST_DELTA}%)"
  echo "     → 라우팅 규칙 점검 고려"
else
  echo "  ✅ Fast 레인 사용률이 안정적입니다 (${FAST_DELTA}%)"
fi

echo ""

echo "5️⃣ Code 레인 비율 변화"
echo "----------------------"
CURRENT_CODE=$(grep "Code_lane_ratio_percent:" "$CURRENT_FILE" | cut -d' ' -f2)
WEEK_AGO_CODE=$(grep "Code_lane_ratio_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
CODE_DELTA=$((CURRENT_CODE - WEEK_AGO_CODE))

echo "  이번 주: ${CURRENT_CODE}%"
echo "  지난 주: ${WEEK_AGO_CODE}%"
echo "  변화: ${CODE_DELTA}%"

if [ $CODE_DELTA -gt 3 ]; then
  echo "  ✅ Code 레인 사용률이 증가했습니다 (+${CODE_DELTA}%)"
elif [ $CODE_DELTA -lt -3 ]; then
  echo "  💡 Code 레인 사용률이 감소했습니다 (${CODE_DELTA}%)"
  echo "     → 코딩 키워드 확장 고려"
else
  echo "  ✅ Code 레인 사용률이 안정적입니다 (${CODE_DELTA}%)"
fi

echo ""

# 전체 요약
echo "📋 주간 변화 요약"
echo "=================="
echo "📊 주요 변화:"
echo "  - P95 응답시간: ${P95_DELTA}ms"
echo "  - 에러율: ${ERROR_DELTA}%"
echo "  - GPU VRAM: ${VRAM_DELTA}%"
echo "  - Fast 레인: ${FAST_DELTA}%"
echo "  - Code 레인: ${CODE_DELTA}%"

echo ""

# 권장사항
echo "🔧 주간 권장사항"
echo "=================="

if [ $P95_DELTA -gt 50 ] || [ $ERROR_DELTA -gt 2 ] || [ $VRAM_DELTA -gt 10 ]; then
  echo "🚨 성능 저하 감지됨"
  echo "   → ./diagnose-issues.sh 실행"
  echo "   → 파라미터 조정 고려"
elif [ $P95_DELTA -lt -50 ] || [ $ERROR_DELTA -lt -2 ] || [ $VRAM_DELTA -lt -10 ]; then
  echo "✅ 성능 개선됨"
  echo "   → 현재 설정 유지"
else
  echo "✅ 성능 안정적"
  echo "   → 정기 모니터링 계속"
fi

echo ""
echo "🎯 주간 비교 완료!"
echo "💡 다음 주 비교: ./weekly-comparison.sh"
