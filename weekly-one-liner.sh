#!/bin/bash

# 📌 운영 한 줄 메모 (주간)
# [W{week}] P95=<ms> Err=<%> VRAMmax=<%> Fast=<%> Code=<%> ΔP95=<ms> ΔErr=<%> ΔVRAM=<%>  → action: <한줄>

set -e

echo "📌 DreamSeed AI 운영 한 줄 메모 (주간)"
echo "======================================"

# 현재 주차 계산
WEEK=$(date +%V)
YEAR=$(date +%Y)

echo "📅 현재 주차: W$WEEK ($YEAR)"
echo ""

# 현재 6줄 데이터 가져오기
echo "📊 현재 주차 데이터 수집 중..."
CURRENT_DATA=$(./6line-summary.sh 2>/dev/null | grep -E "(P95_latency_ms|Error_rate_percent|GPU_VRAM_max_percent|Fast_lane_ratio_percent|Code_lane_ratio_percent)" | sed 's/.*: //')

# 데이터 파싱
P95_LATENCY=$(echo "$CURRENT_DATA" | sed -n '1p')
ERROR_RATE=$(echo "$CURRENT_DATA" | sed -n '2p')
GPU_VRAM_MAX=$(echo "$CURRENT_DATA" | sed -n '3p')
FAST_RATIO=$(echo "$CURRENT_DATA" | sed -n '4p')
CODE_RATIO=$(echo "$CURRENT_DATA" | sed -n '5p')

# 1주 전 데이터 (있는 경우)
WEEK_AGO_DATE=$(date -d '7 days ago' +%Y-%m-%d)
WEEK_AGO_FILE="/tmp/6line-$WEEK_AGO_DATE.txt"

if [ -f "$WEEK_AGO_FILE" ]; then
  echo "📊 1주 전 데이터 비교 중..."
  WEEK_AGO_P95=$(grep "P95_latency_ms:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
  WEEK_AGO_ERROR=$(grep "Error_rate_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
  WEEK_AGO_VRAM=$(grep "GPU_VRAM_max_percent:" "$WEEK_AGO_FILE" | cut -d' ' -f2)
  
  DELTA_P95=$((P95_LATENCY - WEEK_AGO_P95))
  DELTA_ERROR=$((ERROR_RATE - WEEK_AGO_ERROR))
  DELTA_VRAM=$((GPU_VRAM_MAX - WEEK_AGO_VRAM))
else
  DELTA_P95=0
  DELTA_ERROR=0
  DELTA_VRAM=0
fi

# 한 줄 액션 결정
ACTION=""
if [ $P95_LATENCY -gt 200 ]; then
  ACTION="--max-model-len 6144→5120"
elif [ $ERROR_RATE -gt 5 ]; then
  ACTION="--gpu-memory-utilization 0.82→0.75"
elif [ $GPU_VRAM_MAX -gt 90 ]; then
  ACTION="--max-model-len 6144→4096"
elif [ $FAST_RATIO -lt 10 ]; then
  ACTION="fast 키워드 확장"
elif [ $CODE_RATIO -lt 5 ]; then
  ACTION="code 키워드 확장"
else
  ACTION="현재 설정 유지"
fi

# 한 줄 메모 생성
ONE_LINER="[W$WEEK] P95=${P95_LATENCY}ms Err=${ERROR_RATE}% VRAMmax=${GPU_VRAM_MAX}% Fast=${FAST_RATIO}% Code=${CODE_RATIO}% ΔP95=${DELTA_P95}ms ΔErr=${DELTA_ERROR}% ΔVRAM=${DELTA_VRAM}% → action: $ACTION"

echo "📌 이번 주 한 줄 메모"
echo "======================"
echo "$ONE_LINER"
echo ""

# 파일에 저장
MEMO_FILE="/tmp/weekly-memo.txt"
echo "$ONE_LINER" >> "$MEMO_FILE"

echo "💾 메모 저장: $MEMO_FILE"
echo ""

# 최근 4주 메모 보기
echo "📋 최근 4주 메모"
echo "================="
tail -4 "$MEMO_FILE" 2>/dev/null || echo "이전 메모 없음"

echo ""

# 북마크용 템플릿
echo "🔖 북마크용 템플릿"
echo "=================="
echo "[W{week}] P95=<ms> Err=<%> VRAMmax=<%> Fast=<%> Code=<%> ΔP95=<ms> ΔErr=<%> ΔVRAM=<%> → action: <한줄>"
echo ""

# 회의용 요약
echo "📊 회의용 요약"
echo "==============="
echo "이번 주 핵심 지표:"
echo "  - P95 응답시간: ${P95_LATENCY}ms (변화: ${DELTA_P95}ms)"
echo "  - 에러율: ${ERROR_RATE}% (변화: ${DELTA_ERROR}%)"
echo "  - GPU VRAM: ${GPU_VRAM_MAX}% (변화: ${DELTA_VRAM}%)"
echo "  - Fast 레인: ${FAST_RATIO}%"
echo "  - Code 레인: ${CODE_RATIO}%"
echo ""
echo "권장 액션: $ACTION"

echo ""
echo "🎯 한 줄 메모 완료!"
echo "💡 회의에서 이 한 줄만 보여주면 됩니다!"
