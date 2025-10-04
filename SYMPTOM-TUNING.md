# 🎯 증상별 "한 줄" 튜닝

## 📊 **로그 분석 기반 튜닝**

### **빠른 집계 명령어**
```bash
# P95 응답시간
awk '{print $4}' /tmp/router.log | sed 's/latency_ms=//' | sort -n | awk 'NR==int(0.95*NR_saved){print; exit} {NR_saved=NR}'

# 에러율
awk '{print $7}' /tmp/router.log | grep -c 'err=1'

# 자동 분석
./analyze-logs.sh
```

## 🔧 **증상별 한 줄 튜닝**

### **1️⃣ 지연↑ (P95 > 200ms)**
```bash
# 원인: 모델 길이/동시 처리 과부하
# 해결: --max-model-len 6144 → 5120 또는 --max-num-seqs 16 → 12

# start-profile-s.sh 수정
sed -i 's/--max-model-len 6144/--max-model-len 5120/' start-profile-s.sh
sed -i 's/--max-num-seqs 16/--max-num-seqs 12/' start-profile-s.sh
```

### **2️⃣ OOM/종료 (에러율 > 5%)**
```bash
# 원인: GPU 메모리 부족
# 해결: --gpu-memory-utilization 0.82 → 0.80 + 길이 4096

# start-profile-s.sh 수정
sed -i 's/--gpu-memory-utilization 0.82/--gpu-memory-utilization 0.80/' start-profile-s.sh
sed -i 's/--max-model-len 6144/--max-model-len 4096/' start-profile-s.sh
```

### **3️⃣ 짧은 답이 느림**
```bash
# 원인: fast 레인 사용률 낮음
# 해결: fast(8002) 사용 비율↑ or fast 조건에 "짧게/요약" 키워드 추가

# router.py 수정 - fast 조건 강화
sed -i 's/if re.search(r"빠른|간단|요약", prompt, re.IGNORECASE):/if re.search(r"빠른|간단|요약|짧게|한줄|핵심", prompt, re.IGNORECASE):/' router.py
```

### **4️⃣ 코딩 품질 부족**
```bash
# 원인: code 레인 사용률 낮음
# 해결: 8001 온디맨드(Qwen Coder 7B) 더 자주 가동, 라우팅 키워드 보강

# router.py 수정 - 코딩 키워드 강화
sed -i 's/if re.search(r"코드|프로그래밍|함수|클래스|import|def|class", prompt, re.IGNORECASE):/if re.search(r"코드|프로그래밍|함수|클래스|import|def|class|SELECT|테스트|리팩터|디버그|알고리즘", prompt, re.IGNORECASE):/' router.py
```

## 📈 **성능 모니터링**

### **실시간 모니터링**
```bash
# 실시간 로그 모니터링
tail -f /tmp/router.log

# 실시간 성능 분석
watch -n 5 './analyze-logs.sh'
```

### **자동 알림 설정**
```bash
# 헬스체크 실패 시 Slack 알림
./simple-alert.sh

# cron 설정 (5분마다)
echo "*/5 * * * * /home/won/projects/dreamseed_monorepo/simple-alert.sh" | crontab -
```

## 🎯 **튜닝 우선순위**

### **High Priority (즉시 적용)**
1. **P95 > 200ms** → `--max-model-len` 감소
2. **에러율 > 5%** → `--gpu-memory-utilization` 감소
3. **OOM 발생** → 모델 길이 4096으로 제한

### **Medium Priority (1주 내)**
1. **fast 사용률 < 10%** → 키워드 보강
2. **code 사용률 < 5%** → 코딩 키워드 보강
3. **응답시간 편차 큼** → `--max-num-seqs` 조정

### **Low Priority (1개월 내)**
1. **토큰 효율성** → `--max-num-batched-tokens` 조정
2. **동시 처리 최적화** → `--max-num-seqs` 증가
3. **메모리 효율성** → `--dtype` 최적화

## 🔍 **문제 진단 플로우**

### **1단계: 로그 분석**
```bash
./analyze-logs.sh
```

### **2단계: 증상 파악**
- P95 > 200ms → 지연 문제
- 에러율 > 5% → 안정성 문제
- fast 사용률 < 10% → 라우팅 문제
- code 사용률 < 5% → 코딩 라우팅 문제

### **3단계: 한 줄 수정**
```bash
# 지연 문제
sed -i 's/--max-model-len 6144/--max-model-len 5120/' start-profile-s.sh

# 안정성 문제
sed -i 's/--gpu-memory-utilization 0.82/--gpu-memory-utilization 0.80/' start-profile-s.sh

# 라우팅 문제
sed -i 's/if re.search(r"빠른|간단|요약"/if re.search(r"빠른|간단|요약|짧게|한줄|핵심"/' router.py
```

### **4단계: 재시작 및 검증**
```bash
./stop-profile-s.sh
./start-profile-s.sh
sleep 60
./load-test-10.sh
```

## 📊 **성능 목표**

### **기본 목표**
- **P95 응답시간**: < 200ms
- **에러율**: < 1%
- **가용성**: > 99.9%
- **동시 처리**: 16개 요청

### **최적화 목표**
- **P95 응답시간**: < 100ms
- **에러율**: < 0.1%
- **가용성**: > 99.99%
- **동시 처리**: 20개 요청

## 🚀 **다음 스텝 (선택)**

### **RAG 미니**
```bash
# 임베딩(가용 7B) + pgvector로 FAQ 정확도↑
docker run --gpus all --rm -p 8003:8003 \
  vllm/vllm-openai:latest \
  --model sentence-transformers/all-MiniLM-L6-v2 \
  --port 8003
```

### **온디맨드 7B 자동화**
```bash
# 라우터에서 볼륨/키워드 감지 시 8001 auto up/down
./auto-scale-7b.sh
```

### **70B 클라우드 분기**
```bash
# 수요 늘면 Lambda 2×A100 80GB → general70 조건 분기
# router.py에 general70 백엔드 추가
```

---

**💡 이 가이드를 따라하면 데이터 기반 미세 조정이 쉬워집니다!** 🎯
