#!/bin/bash

# 📥 운영 데이터 6줄 자동 요약 (복붙 템플릿)
# analyze-logs.sh가 위 6줄 요약을 stdout으로 내도록 추가

set -e

LOG_FILE="/tmp/router.log"

echo "📥 DreamSeed AI 운영 데이터 6줄 요약"
echo "========================================"

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

echo "📋 분석 기간: $(head -1 "$LOG_FILE" | cut -d'=' -f2 | cut -d'T' -f1) ~ $(tail -1 "$LOG_FILE" | cut -d'=' -f2 | cut -d'T' -f1)"
echo "📋 총 요청 수: $LOG_SIZE"
echo ""

# 1) P95 응답시간
echo "1️⃣ P95 응답시간 계산 중..."
P95_LATENCY=$(awk '{print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | sort -n | awk 'NR==int(0.95*NR_saved){print; exit} {NR_saved=NR}')
if [ -z "$P95_LATENCY" ]; then
  P95_LATENCY=0
fi

# 2) 에러율
echo "2️⃣ 에러율 계산 중..."
ERROR_COUNT=$(awk '{print $7}' "$LOG_FILE" | grep -c 'err=1' || echo "0")
ERROR_RATE=$((ERROR_COUNT * 100 / LOG_SIZE))

# 3) GPU VRAM 최대 사용률
echo "3️⃣ GPU VRAM 상태 확인 중..."
GPU_VRAM_MAX=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "%.0f", ($1/$2)*100}')

# 4) 평균 토큰 수
echo "4️⃣ 평균 토큰 수 계산 중..."
AVG_TOKENS_IN=$(awk '{print $5}' "$LOG_FILE" | sed 's/tokens_in=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
AVG_TOKENS_OUT=$(awk '{print $6}' "$LOG_FILE" | sed 's/tokens_out=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')

# 5) Fast 레인 비율
echo "5️⃣ Fast 레인 비율 계산 중..."
FAST_COUNT=$(awk '$2=="lane=fast"' "$LOG_FILE" | wc -l)
FAST_RATIO=$((FAST_COUNT * 100 / LOG_SIZE))

# 6) Code 레인 비율
echo "6️⃣ Code 레인 비율 계산 중..."
CODE_COUNT=$(awk '$2=="lane=code"' "$LOG_FILE" | wc -l)
CODE_RATIO=$((CODE_COUNT * 100 / LOG_SIZE))

echo ""
echo "🎯 운영 데이터 6줄 요약 (복붙 템플릿)"
echo "========================================"
echo "P95_latency_ms: $P95_LATENCY"
echo "Error_rate_percent: $ERROR_RATE"
echo "GPU_VRAM_max_percent: $GPU_VRAM_MAX"
echo "Avg_tokens_in/out: $AVG_TOKENS_IN/$AVG_TOKENS_OUT"
echo "Fast_lane_ratio_percent: $FAST_RATIO"
echo "Code_lane_ratio_percent: $CODE_RATIO"
echo ""

# 자동 진단 및 권장사항
echo "🔧 자동 진단 및 권장사항"
echo "=========================="

# P95 지연 문제
if [ $P95_LATENCY -gt 200 ]; then
  echo "⚠️  P95 지연 문제 (${P95_LATENCY}ms > 200ms)"
  echo "   → --max-model-len 6144 → 5120 또는 --max-num-seqs 16 → 12 (지연 ↓)"
fi

# 에러율 문제
if [ $ERROR_RATE -gt 1 ]; then
  echo "🚨 에러율 문제 (${ERROR_RATE}% > 1%)"
  if [ $ERROR_RATE -gt 5 ]; then
    echo "   → --gpu-memory-utilization 0.82 → 0.80 + 길이 4096"
  else
    echo "   → 라우터 timeout read: 90 → 120, 재시도 1회 추가"
  fi
fi

# VRAM 문제
if [ $GPU_VRAM_MAX -gt 90 ]; then
  echo "🚨 VRAM 부족 (${GPU_VRAM_MAX}% > 90%)"
  echo "   → --gpu-memory-utilization 0.82 → 0.80 + 길이 4096"
fi

# Fast 레인 사용률 낮음
if [ $FAST_RATIO -lt 10 ]; then
  echo "💡 Fast 레인 사용률 낮음 (${FAST_RATIO}% < 10%)"
  echo "   → fast 키워드 확대(짧게|핵심|한줄|요약) + 8002(Mini) 웜업"
fi

# Code 레인 사용률 낮음
if [ $CODE_RATIO -lt 5 ]; then
  echo "💡 Code 레인 사용률 낮음 (${CODE_RATIO}% < 5%)"
  echo "   → 8001 Qwen Coder 온디맨드 활성 빈도↑ + 라우팅 키워드 강화(SELECT|테스트|리팩터|디버그|알고리즘)"
fi

# 정상 상태
if [ $P95_LATENCY -le 200 ] && [ $ERROR_RATE -le 1 ] && [ $GPU_VRAM_MAX -le 90 ]; then
  echo "✅ 모든 지표가 정상 범위입니다!"
  if [ $P95_LATENCY -lt 100 ]; then
    echo "   → 성능 여유 있음: --max-num-seqs 16 → 20 (스루풋↑)"
  fi
fi

echo ""
echo "💡 이 6줄을 복사해서 보내주시면 정확한 '한 줄' 처방을 제안드립니다!"

# A/B 비교용 스냅샷 저장 (1주 단위)
OUT="/tmp/6line-$(date +%Y-%m-%d).txt"
echo "📸 스냅샷 저장 중: $OUT"
cat > "$OUT" << EOF
# DreamSeed AI 6줄 요약 스냅샷 - $(date '+%Y-%m-%d %H:%M:%S')
P95_latency_ms: $P95_LATENCY
Error_rate_percent: $ERROR_RATE
GPU_VRAM_max_percent: $GPU_VRAM_MAX
Avg_tokens_in/out: $AVG_TOKENS_IN/$AVG_TOKENS_OUT
Fast_lane_ratio_percent: $FAST_RATIO
Code_lane_ratio_percent: $CODE_RATIO
EOF

echo "✅ 스냅샷 저장 완료: $OUT"
echo "💡 주간 비교: diff /tmp/6line-$(date -d '7 days ago' +%Y-%m-%d).txt $OUT"
