#!/bin/bash

# 🔒 운영 위생 체크리스트 (필수)

set -e

echo "🔒 DreamSeed AI 운영 위생 점검"
echo "================================"

# 1) HF 토큰 관리
echo "1️⃣ Hugging Face 토큰 관리"
echo "---------------------------"
if [ -f ".env" ]; then
  if grep -q "HF_TOKEN" .env; then
    echo "✅ .env 파일에 HF_TOKEN이 설정되어 있습니다"
  else
    echo "⚠️  .env 파일에 HF_TOKEN이 없습니다"
    echo "   권장: echo 'HF_TOKEN=hf_your_token_here' >> .env"
  fi
else
  echo "⚠️  .env 파일이 없습니다"
  echo "   권장: touch .env && echo 'HF_TOKEN=hf_your_token_here' >> .env"
fi

# .env 파일이 Git에 커밋되지 않았는지 확인
if [ -f ".gitignore" ]; then
  if grep -q "\.env" .gitignore; then
    echo "✅ .env가 .gitignore에 포함되어 있습니다"
  else
    echo "⚠️  .env가 .gitignore에 없습니다"
    echo "   권장: echo '.env' >> .gitignore"
  fi
else
  echo "⚠️  .gitignore 파일이 없습니다"
  echo "   권장: echo '.env' > .gitignore"
fi

echo ""

# 2) 포트 보안
echo "2️⃣ 포트 보안"
echo "-------------"
echo "📊 현재 열린 포트:"
netstat -tlnp | grep -E ":800[0-2]|:8010" || echo "관련 포트 없음"

echo ""
echo "🔒 보안 권장사항:"
echo "   - 8000/8001/8002는 내부망 전용"
echo "   - 8010(라우터)만 LB/HTTPS로 공개"
echo "   - 방화벽 설정: sudo ufw deny 8000:8002/tcp"

echo ""

# 3) 캐시 디스크 여유
echo "3️⃣ 캐시 디스크 여유"
echo "-------------------"
echo "📊 디스크 사용량:"
df -h | awk 'NR==1 || /cache|home|\/$/'

echo ""
echo "📊 HF 캐시 크기:"
if [ -d "$HOME/.cache/huggingface" ]; then
  CACHE_SIZE=$(du -sh $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  CACHE_SIZE_GB=$(du -sg $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  echo "   캐시 크기: $CACHE_SIZE"
  
  if [ -n "$CACHE_SIZE_GB" ] && [ $CACHE_SIZE_GB -gt 50 ]; then
    echo "⚠️  캐시 크기가 50GB를 초과했습니다 ($CACHE_SIZE_GB GB)"
    echo "   권장: rm -rf ~/.cache/huggingface/*"
  else
    echo "✅ 캐시 크기가 적절합니다 ($CACHE_SIZE_GB GB)"
  fi
else
  echo "❌ 캐시 디렉터리 없음"
fi

echo ""

# 4) 로그 파일 관리
echo "4️⃣ 로그 파일 관리"
echo "-------------------"
echo "📊 로그 파일 상태:"
for log_file in "/tmp/router.log" "/tmp/dreamseed-*.log"; do
  if [ -f "$log_file" ]; then
    LOG_SIZE=$(wc -l < "$log_file" 2>/dev/null || echo "0")
    LOG_SIZE_MB=$(du -sm "$log_file" 2>/dev/null | cut -f1)
    echo "   $log_file: $LOG_SIZE 라인, ${LOG_SIZE_MB}MB"
  else
    echo "   $log_file: 없음"
  fi
done

echo ""
echo "🔧 로그 관리 권장사항:"
echo "   - 로그 로테이션 설정: /etc/logrotate.d/dreamseed"
echo "   - 30일 이상 보관"
echo "   - 압축 저장"

echo ""

# 5) 시스템 리소스
echo "5️⃣ 시스템 리소스"
echo "-------------------"
echo "📊 메모리 사용량:"
free -h | awk 'NR==2{printf "   메모리: %s / %s (%.1f%% 사용)\n", $3, $2, ($3/$2)*100}'

echo ""
echo "📊 GPU 메모리:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "   GPU: %dMB / %dMB (%.1f%% 사용)\n", $1, $2, ($1/$2)*100}'

echo ""

# 6) 보안 체크리스트
echo "6️⃣ 보안 체크리스트"
echo "-------------------"
echo "✅ 필수 보안 항목:"
echo "   [ ] HF 토큰을 .env 파일에 저장"
echo "   [ ] .env 파일을 .gitignore에 추가"
echo "   [ ] 8000-8002 포트를 내부망 전용으로 설정"
echo "   [ ] 8010 포트만 외부 공개 (LB/HTTPS)"
echo "   [ ] 방화벽 설정 (ufw 또는 iptables)"
echo "   [ ] 정기적인 보안 업데이트"
echo "   [ ] 로그 모니터링 설정"

echo ""

# 7) 백업 체크리스트
echo "7️⃣ 백업 체크리스트"
echo "-------------------"
echo "✅ 필수 백업 항목:"
echo "   [ ] 설정 파일 백업 (.env, 스크립트)"
echo "   [ ] 모델 캐시 백업 (선택사항)"
echo "   [ ] 로그 파일 백업"
echo "   [ ] 데이터베이스 백업 (RAG 사용 시)"

echo ""

# 8) 모니터링 체크리스트
echo "8️⃣ 모니터링 체크리스트"
echo "-----------------------"
echo "✅ 필수 모니터링 항목:"
echo "   [ ] 헬스체크 자동화 (cron)"
echo "   [ ] 알림 설정 (Slack/Discord)"
echo "   [ ] 로그 분석 자동화"
echo "   [ ] 성능 메트릭 수집"
echo "   [ ] 에러율 모니터링"

echo ""

# 9) 권장사항 요약
echo "🔧 권장사항 요약"
echo "=================="

# 보안 강화
echo "🔒 보안 강화:"
echo "   - 방화벽 설정: sudo ufw enable"
echo "   - 포트 제한: sudo ufw deny 8000:8002/tcp"
echo "   - HTTPS 설정: Nginx/Apache 리버스 프록시"

# 모니터링 강화
echo ""
echo "📊 모니터링 강화:"
echo "   - 헬스체크 자동화: crontab -e"
echo "   - 로그 분석: ./analyze-logs.sh"
echo "   - 알림 설정: ./simple-alert.sh"

# 성능 최적화
echo ""
echo "⚡ 성능 최적화:"
echo "   - 캐시 정리: ./cache-monitor.sh"
echo "   - 로그 분석: ./analyze-logs.sh"
echo "   - 부하 테스트: ./load-test-10.sh"

echo ""
echo "🎯 운영 위생 점검 완료!"
echo "💡 정기 점검: 주 1회 실행 권장"
