#!/bin/bash

# 🔧 자동 미세 조정 프롬프트 생성
# 6줄 데이터를 받아서 정확한 "한 줄" 처방 제안

set -e

echo "🔧 DreamSeed AI 자동 미세 조정 프롬프트"
echo "========================================"

# 사용법 안내
if [ $# -eq 0 ]; then
  echo "사용법: $0 <6줄_데이터>"
  echo ""
  echo "예시:"
  echo "$0 \"P95_latency_ms: 230\" \"Error_rate_percent: 0.8\" \"GPU_VRAM_max_percent: 76\" \"Avg_tokens_in/out: 45/120\" \"Fast_lane_ratio_percent: 8\" \"Code_lane_ratio_percent: 3\""
  echo ""
  echo "또는 6line-summary.sh 실행 후 결과를 복사해서 사용:"
  echo "./6line-summary.sh"
  exit 1
fi

# 6줄 데이터 파싱
P95_LATENCY=$(echo "$1" | grep -o 'P95_latency_ms: [0-9]*' | cut -d' ' -f2)
ERROR_RATE=$(echo "$2" | grep -o 'Error_rate_percent: [0-9]*' | cut -d' ' -f2)
GPU_VRAM_MAX=$(echo "$3" | grep -o 'GPU_VRAM_max_percent: [0-9]*' | cut -d' ' -f2)
TOKENS_IN=$(echo "$4" | grep -o 'Avg_tokens_in/out: [0-9]*' | cut -d' ' -f2)
TOKENS_OUT=$(echo "$4" | grep -o 'Avg_tokens_in/out: [0-9]*/[0-9]*' | cut -d'/' -f2)
FAST_RATIO=$(echo "$5" | grep -o 'Fast_lane_ratio_percent: [0-9]*' | cut -d' ' -f2)
CODE_RATIO=$(echo "$6" | grep -o 'Code_lane_ratio_percent: [0-9]*' | cut -d' ' -f2)

echo "📊 파싱된 데이터:"
echo "  P95 지연: ${P95_LATENCY}ms"
echo "  에러율: ${ERROR_RATE}%"
echo "  GPU VRAM: ${GPU_VRAM_MAX}%"
echo "  토큰: ${TOKENS_IN}/${TOKENS_OUT}"
echo "  Fast 비율: ${FAST_RATIO}%"
echo "  Code 비율: ${CODE_RATIO}%"
echo ""

echo "🎯 정확한 '한 줄' 처방 제안"
echo "============================="

# 1) P95 지연 문제 (우선순위 1)
if [ $P95_LATENCY -gt 200 ]; then
  echo "🚨 P95 지연 문제 (${P95_LATENCY}ms > 200ms)"
  if [ $P95_LATENCY -gt 300 ]; then
    echo "   → --max-model-len 6144 → 4096 (급한 조치)"
  else
    echo "   → --max-model-len 6144 → 5120 (점진적 조치)"
  fi
  echo "   → --max-num-seqs 16 → 12 (동시 처리 감소)"
  echo ""
fi

# 2) 에러율 문제 (우선순위 2)
if [ $ERROR_RATE -gt 1 ]; then
  echo "🚨 에러율 문제 (${ERROR_RATE}% > 1%)"
  if [ $ERROR_RATE -gt 5 ]; then
    echo "   → --gpu-memory-utilization 0.82 → 0.75 (메모리 여유 확보)"
    echo "   → --max-model-len 6144 → 4096 (길이 제한)"
  else
    echo "   → 라우터 timeout read: 90 → 120 (타임아웃 연장)"
    echo "   → 재시도 1회 추가 (안정성 향상)"
  fi
  echo ""
fi

# 3) VRAM 문제 (우선순위 3)
if [ $GPU_VRAM_MAX -gt 90 ]; then
  echo "🚨 VRAM 부족 (${GPU_VRAM_MAX}% > 90%)"
  echo "   → --gpu-memory-utilization 0.82 → 0.80 (메모리 사용률 감소)"
  echo "   → --max-model-len 6144 → 4096 (모델 길이 제한)"
  echo ""
fi

# 4) Fast 레인 사용률 낮음
if [ $FAST_RATIO -lt 10 ]; then
  echo "💡 Fast 레인 사용률 낮음 (${FAST_RATIO}% < 10%)"
  echo "   → fast 키워드 확대: '짧게|핵심|한줄|요약|간단' 추가"
  echo "   → 8002(Mini) 웜업 호출 추가"
  echo ""
fi

# 5) Code 레인 사용률 낮음
if [ $CODE_RATIO -lt 5 ]; then
  echo "💡 Code 레인 사용률 낮음 (${CODE_RATIO}% < 5%)"
  echo "   → 8001 Qwen Coder 온디맨드 활성 빈도↑"
  echo "   → 라우팅 키워드 강화: 'SELECT|테스트|리팩터|디버그|알고리즘' 추가"
  echo ""
fi

# 6) 토큰 효율성 분석
TOKEN_RATIO=$((TOKENS_OUT * 100 / TOKENS_IN))
if [ $TOKEN_RATIO -lt 200 ]; then
  echo "💡 토큰 효율성 낮음 (출력/입력 비율: ${TOKEN_RATIO}%)"
  echo "   → max_tokens 제한: 256~512 (짧은 응답 유도)"
  echo ""
fi

# 7) 정상 상태일 때 최적화 제안
if [ $P95_LATENCY -le 200 ] && [ $ERROR_RATE -le 1 ] && [ $GPU_VRAM_MAX -le 90 ]; then
  echo "✅ 모든 지표가 정상 범위입니다!"
  if [ $P95_LATENCY -lt 100 ]; then
    echo "   → 성능 여유 있음: --max-num-seqs 16 → 20 (스루풋↑)"
  fi
  if [ $GPU_VRAM_MAX -lt 70 ]; then
    echo "   → 메모리 여유 있음: --max-model-len 6144 → 8192 (길이↑)"
  fi
  echo ""
fi

# 8) 실행 명령어 생성
echo "🔧 실행 명령어 (복사해서 실행)"
echo "================================"

if [ $P95_LATENCY -gt 200 ]; then
  echo "# 지연 문제 해결"
  echo "sed -i 's/--max-model-len 6144/--max-model-len 5120/' start-profile-s.sh"
  echo "sed -i 's/--max-num-seqs 16/--max-num-seqs 12/' start-profile-s.sh"
  echo "./stop-profile-s.sh && ./start-profile-s.sh"
  echo ""
fi

if [ $ERROR_RATE -gt 5 ]; then
  echo "# 안정성 문제 해결"
  echo "sed -i 's/--gpu-memory-utilization 0.82/--gpu-memory-utilization 0.75/' start-profile-s.sh"
  echo "sed -i 's/--max-model-len 6144/--max-model-len 4096/' start-profile-s.sh"
  echo "./stop-profile-s.sh && ./start-profile-s.sh"
  echo ""
fi

if [ $FAST_RATIO -lt 10 ]; then
  echo "# Fast 레인 사용률 향상"
  echo "sed -i 's/if re.search(r\"빠른|간단|요약\"/if re.search(r\"빠른|간단|요약|짧게|핵심|한줄\"/' router.py"
  echo ""
fi

if [ $CODE_RATIO -lt 5 ]; then
  echo "# Code 레인 사용률 향상"
  echo "sed -i 's/if re.search(r\"코드|프로그래밍|함수|클래스|import|def|class\"/if re.search(r\"코드|프로그래밍|함수|클래스|import|def|class|SELECT|테스트|리팩터|디버그|알고리즘\"/' router.py"
  echo ""
fi

echo "🎯 처방 완료!"
echo "💡 변경 후: ./load-test-10.sh로 성능 검증"
