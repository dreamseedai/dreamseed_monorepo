# 🎯 DreamSeed AI 최종 운영 가이드

## 📥 **운영 데이터 6줄 (복붙 템플릿)**

### **자동 생성**
```bash
# 6줄 요약 자동 생성
./6line-summary.sh
```

### **수동 입력 형식**
```
P95_latency_ms: <값>
Error_rate_percent: <값>
GPU_VRAM_max_percent: <값>
Avg_tokens_in/out: <in>/<out>
Fast_lane_ratio_percent: <값>
Code_lane_ratio_percent: <값>
```

### **예시**
```
P95_latency_ms: 230
Error_rate_percent: 0.8
GPU_VRAM_max_percent: 76
Avg_tokens_in/out: 45/120
Fast_lane_ratio_percent: 8
Code_lane_ratio_percent: 3
```

## 🔧 **자동 미세 조정 프롬프트**

### **6줄 데이터로 정확한 처방**
```bash
# 6줄 데이터를 받아서 정확한 "한 줄" 처방 제안
./auto-tuning-prompt.sh "P95_latency_ms: 230" "Error_rate_percent: 0.8" "GPU_VRAM_max_percent: 76" "Avg_tokens_in/out: 45/120" "Fast_lane_ratio_percent: 8" "Code_lane_ratio_percent: 3"
```

### **처방 예시**

#### **P95가 220ms↑**
```bash
→ --max-model-len 6144 → 5120 또는 --max-num-seqs 16 → 12 (지연 ↓)
sed -i 's/--max-model-len 6144/--max-model-len 5120/' start-profile-s.sh
```

#### **에러율이 1%↑ & 타임아웃↑**
```bash
→ 라우터 timeout read: 90 → 120, 재시도 1회 추가
```

#### **VRAM Max 90%↑**
```bash
→ --gpu-memory-utilization 0.82 → 0.80 + 길이 4096
sed -i 's/--gpu-memory-utilization 0.82/--gpu-memory-utilization 0.80/' start-profile-s.sh
```

#### **짧은 질문 많은데도 느림**
```bash
→ fast 키워드 확대(짧게|핵심|한줄|요약) + 8002(Mini) 웜업
sed -i 's/if re.search(r"빠른|간단|요약"/if re.search(r"빠른|간단|요약|짧게|핵심|한줄\"/' router.py
```

#### **코딩 품질 아쉬움**
```bash
→ 8001 Qwen Coder 온디맨드 활성 빈도↑ + 라우팅 키워드 강화(SELECT|테스트|리팩터|디버그|알고리즘)
sed -i 's/if re.search(r"코드|프로그래밍|함수|클래스|import|def|class\"/if re.search(r"코드|프로그래밍|함수|클래스|import|def|class|SELECT|테스트|리팩터|디버그|알고리즘\"/' router.py
```

## 🧪 **자동화 힌트**

### **일일 리포트 자동화**
```bash
# cron으로 하루 1회 실행 → Slack으로 붙여 숫자만 알림
./daily-report.sh
```

### **cron 설정**
```bash
# 자동화 설정
./setup-cron.sh

# 권장 cron 작업
0 9 * * * /home/won/projects/dreamseed_monorepo/daily-report.sh      # 일일 리포트
*/5 * * * * /home/won/projects/dreamseed_monorepo/simple-alert.sh    # 헬스체크
0 18 * * * /home/won/projects/dreamseed_monorepo/6line-summary.sh    # 로그 분석
0 8 * * 1 /home/won/projects/dreamseed_monorepo/cache-monitor.sh     # 캐시 모니터링
```

### **Slack 알림 설정**
```bash
# Slack 웹훅 URL 설정
export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'
echo 'export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."' >> ~/.bashrc
```

## 🎯 **운영 워크플로우**

### **일일 점검 (5분)**
1. **6줄 요약 확인**
   ```bash
   ./6line-summary.sh
   ```

2. **문제 발견 시 자동 처방**
   ```bash
   ./auto-tuning-prompt.sh "6줄_데이터"
   ```

3. **처방 실행**
   ```bash
   # 제안된 명령어 복사해서 실행
   sed -i 's/--max-model-len 6144/--max-model-len 5120/' start-profile-s.sh
   ./stop-profile-s.sh && ./start-profile-s.sh
   ```

4. **성능 검증**
   ```bash
   ./load-test-10.sh
   ```

### **주간 점검 (15분)**
1. **운영 위생 점검**
   ```bash
   ./operation-hygiene.sh
   ```

2. **캐시 모니터링**
   ```bash
   ./cache-monitor.sh
   ```

3. **로그 분석**
   ```bash
   ./analyze-logs.sh
   ```

## 📊 **성능 목표**

### **기본 목표**
- **P95 응답시간**: < 200ms
- **에러율**: < 1%
- **GPU VRAM**: < 90%
- **Fast 레인 비율**: > 10%
- **Code 레인 비율**: > 5%

### **최적화 목표**
- **P95 응답시간**: < 100ms
- **에러율**: < 0.1%
- **GPU VRAM**: < 80%
- **Fast 레인 비율**: > 15%
- **Code 레인 비율**: > 10%

## 🚀 **바로 사용 가능한 명령어**

### **성능 분석**
```bash
# 6줄 요약
./6line-summary.sh

# 자동 처방
./auto-tuning-prompt.sh "6줄_데이터"

# 로그 분석
./analyze-logs.sh

# 부하 테스트
./load-test-10.sh
```

### **운영 점검**
```bash
# 헬스체크
./health-check-60s.sh

# 운영 위생
./operation-hygiene.sh

# 캐시 모니터링
./cache-monitor.sh

# 진단
./diagnose-issues.sh
```

### **자동화**
```bash
# 일일 리포트
./daily-report.sh

# 알림 설정
./simple-alert.sh

# cron 설정
./setup-cron.sh
```

## 🎯 **첫 주 운영 체크리스트**

### **일일 점검 (5분)**
- [ ] `./6line-summary.sh` - 6줄 데이터 확인
- [ ] `./auto-tuning-prompt.sh` - 문제 시 자동 처방
- [ ] `./load-test-10.sh` - 성능 검증

### **주간 점검 (15분)**
- [ ] `./operation-hygiene.sh` - 보안/위생 점검
- [ ] `./cache-monitor.sh` - 캐시 크기 < 50GB
- [ ] `./analyze-logs.sh` - 에러 패턴 파악

### **월간 점검 (30분)**
- [ ] 모델 성능 평가
- [ ] 비용 최적화 검토
- [ ] 확장 필요성 검토

---

**💡 이제 진짜 "켜면 돈 되는" 상태에서 숫자로 미세 조정만 하면 됩니다!** 🚀

**첫 주 지표 6줄만 주시면, 그 값에 맞춰 "정확히 한 줄" 바로 제안드릴게요!** 🎯
