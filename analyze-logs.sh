#!/bin/bash

# 📊 빠른 집계 (P95·에러율·토큰량 바로 산출)

set -e

LOG_FILE="/tmp/router.log"

echo "📊 DreamSeed AI 로그 분석"
echo "================================"

if [ ! -f "$LOG_FILE" ]; then
  echo "❌ 로그 파일이 없습니다: $LOG_FILE"
  echo "💡 라우터를 실행하고 요청을 보내면 로그가 생성됩니다."
  exit 1
fi

# 로그 파일 크기 확인
LOG_SIZE=$(wc -l < "$LOG_FILE")
echo "📋 총 로그 라인 수: $LOG_SIZE"

if [ $LOG_SIZE -eq 0 ]; then
  echo "❌ 로그가 비어있습니다."
  exit 1
fi

echo ""

# 1) P95 응답시간
echo "1️⃣ P95 응답시간"
echo "-------------------"
P95_LATENCY=$(awk '{print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | sort -n | awk 'NR==int(0.95*NR_saved){print; exit} {NR_saved=NR}')
if [ -n "$P95_LATENCY" ]; then
  echo "📊 P95 응답시간: ${P95_LATENCY}ms"
  
  if [ $P95_LATENCY -gt 200 ]; then
    echo "⚠️  P95가 높습니다 (${P95_LATENCY}ms > 200ms)"
    echo "   권장: --max-model-len 6144 → 5120"
    echo "   권장: --max-num-seqs 16 → 12"
  elif [ $P95_LATENCY -lt 50 ]; then
    echo "✅ P95가 빠릅니다 (${P95_LATENCY}ms < 50ms)"
    echo "   여유가 있다면: --max-num-seqs 16 → 20 (스루풋↑)"
  else
    echo "✅ P95가 적절합니다 (${P95_LATENCY}ms)"
  fi
else
  echo "❌ P95 계산 실패"
fi

echo ""

# 2) 에러율
echo "2️⃣ 에러율"
echo "-------------"
ERROR_COUNT=$(awk '{print $7}' "$LOG_FILE" | grep -c 'err=1' || echo "0")
TOTAL_COUNT=$LOG_SIZE
ERROR_RATE=$((ERROR_COUNT * 100 / TOTAL_COUNT))

echo "📊 에러 수: $ERROR_COUNT / $TOTAL_COUNT"
echo "📊 에러율: ${ERROR_RATE}%"

if [ $ERROR_RATE -gt 5 ]; then
  echo "🚨 에러율이 높습니다 (${ERROR_RATE}% > 5%)"
  echo "   권장: ./diagnose-issues.sh 실행"
  echo "   권장: --gpu-memory-utilization 0.82 → 0.75"
elif [ $ERROR_RATE -gt 1 ]; then
  echo "⚠️  에러율이 약간 높습니다 (${ERROR_RATE}% > 1%)"
  echo "   권장: 모니터링 강화"
else
  echo "✅ 에러율이 정상입니다 (${ERROR_RATE}% ≤ 1%)"
fi

echo ""

# 3) 평균 응답시간
echo "3️⃣ 평균 응답시간"
echo "-------------------"
AVG_LATENCY=$(awk '{print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
echo "📊 평균 응답시간: ${AVG_LATENCY}ms"

echo ""

# 4) 레인별 통계
echo "4️⃣ 레인별 통계"
echo "-------------------"
echo "📊 레인별 요청 수:"
awk '{print $2}' "$LOG_FILE" | sed 's/lane=//' | sort | uniq -c | sort -nr

echo ""
echo "📊 레인별 평균 응답시간:"
for lane in general code fast; do
  LANE_AVG=$(awk -v lane="$lane" '$2=="lane="lane {print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
  LANE_COUNT=$(awk -v lane="$lane" '$2=="lane="lane' "$LOG_FILE" | wc -l)
  echo "  $lane: ${LANE_AVG}ms ($LANE_COUNT회)"
done

echo ""

# 5) 토큰 통계
echo "5️⃣ 토큰 통계"
echo "-------------------"
AVG_TOKENS_IN=$(awk '{print $5}' "$LOG_FILE" | sed 's/tokens_in=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
AVG_TOKENS_OUT=$(awk '{print $6}' "$LOG_FILE" | sed 's/tokens_out=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')

echo "📊 평균 입력 토큰: ${AVG_TOKENS_IN}"
echo "📊 평균 출력 토큰: ${AVG_TOKENS_OUT}"

echo ""

# 6) 최근 1시간 통계
echo "6️⃣ 최근 1시간 통계"
echo "-------------------"
RECENT_COUNT=$(awk -v cutoff="$(date -d '1 hour ago' -Iseconds)" '$1 > "ts="cutoff' "$LOG_FILE" | wc -l)
echo "📊 최근 1시간 요청 수: $RECENT_COUNT"

if [ $RECENT_COUNT -gt 0 ]; then
  RECENT_AVG=$(awk -v cutoff="$(date -d '1 hour ago' -Iseconds)" '$1 > "ts="cutoff {print $4}' "$LOG_FILE" | sed 's/latency_ms=//' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print 0}')
  echo "📊 최근 1시간 평균 응답시간: ${RECENT_AVG}ms"
fi

echo ""

# 7) 권장사항
echo "🔧 권장사항"
echo "============="

# 지연이 높은 경우
if [ $P95_LATENCY -gt 200 ]; then
  echo "⚠️  지연↑ → --max-model-len 6144 → 5120 또는 --max-num-seqs 16 → 12"
fi

# 에러율이 높은 경우
if [ $ERROR_RATE -gt 5 ]; then
  echo "🚨 OOM/종료 → --gpu-memory-utilization 0.82 → 0.80 + 길이 4096"
fi

# 짧은 답이 느린 경우
FAST_COUNT=$(awk '$2=="lane=fast"' "$LOG_FILE" | wc -l)
if [ $FAST_COUNT -lt $((TOTAL_COUNT / 10)) ]; then
  echo "💡 짧은 답이 느림 → fast(8002) 사용 비율↑ or fast 조건에 \"짧게/요약\" 키워드 추가"
fi

# 코딩 품질 부족
CODE_COUNT=$(awk '$2=="lane=code"' "$LOG_FILE" | wc -l)
if [ $CODE_COUNT -lt $((TOTAL_COUNT / 20)) ]; then
  echo "💡 코딩 품질 부족 → 8001 온디맨드(Qwen Coder 7B) 더 자주 가동, 라우팅 키워드 보강"
fi

echo ""
echo "🎯 분석 완료!"
echo "💡 실시간 모니터링: tail -f $LOG_FILE"
