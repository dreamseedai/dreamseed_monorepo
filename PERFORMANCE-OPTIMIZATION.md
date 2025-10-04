# ⚡ 성능 최적화 가이드

## 🎯 **적용된 최적화**

### 1️⃣ **로딩·속도 최적화 (체감 효과 큼)**

#### **모델 캐시 디렉터리 명시 + 권한**
```bash
# docker run에 추가
-v $HOME/.cache/huggingface:/root/.cache/huggingface \
--env HF_HOME=/root/.cache/huggingface \
--shm-size=2g
```

#### **vLLM 런타임 튜닝 (지연/스루풋)**
```bash
--gpu-memory-utilization 0.82    # 안정 여유
--max-model-len 6144             # 성능/안정성 밸런스
--max-num-seqs 16                # 동시 처리 수
--max-num-batched-tokens 2048    # 토큰 배치 상한
```

#### **웜업 호출 (콜드스타트 방지)**
```bash
# 시작 스크립트에서 각 포트에 1회씩 호출
curl -s http://127.0.0.1:8000/v1/models >/dev/null
```

### 2️⃣ **종료·에러 가드 (무중단 운영)**

#### **라우터 타임아웃/재시도/폴백 강화**
```python
# httpx 클라이언트 생성부
timeout = httpx.Timeout(connect=10, read=90, write=90, pool=10)
# 3단계 폴백: general→fast→general
```

#### **컨테이너 자동 재기동**
```bash
# docker compose에서
restart: unless-stopped
```

### 3️⃣ **진단 포인트 (컨테이너 종료 시 90% 원인)**

#### **즉시 진단 명령어**
```bash
# 컨테이너 로그
docker logs <container> --tail 200

# OOM Kill 여부
dmesg | tail -n 50

# GPU 상태
nvidia-smi

# 디스크 여유
df -h
```

#### **자동 진단 스크립트**
```bash
./diagnose-issues.sh
```

## 🔧 **문제별 해결책**

### **OOM (Out of Memory)**
- **증상**: 컨테이너 갑자기 종료
- **해결**: 
  - `--gpu-memory-utilization 0.82 → 0.75`
  - `--max-model-len 6144 → 4096`
  - `--max-num-seqs 16 → 8`

### **HF 다운로드 실패**
- **증상**: 모델 로딩 실패, 403/404 에러
- **해결**: 
  - 토큰/네트워크 확인
  - 캐시 볼륨 유지 + 재시도
  - `--env HF_HOME=/root/.cache/huggingface`

### **권한/포트 문제**
- **증상**: 포트 바인딩 실패
- **해결**: 
  - 포트 변경/권한 확인
  - `sudo chown -R $USER:$USER ~/.cache/huggingface`

## 📊 **성능 모니터링**

### **주요 메트릭**
- **응답 시간**: P95 < 100ms
- **에러율**: < 1%
- **GPU 메모리**: < 90%
- **동시 처리**: 16개 요청

### **모니터링 명령어**
```bash
# 실시간 GPU 모니터링
watch -n 1 nvidia-smi

# 응답 시간 테스트
./smoke-test.sh

# 전체 시스템 점검
./health-check-60s.sh
```

## 🚀 **다음 최적화 루틴**

### **1주간 실사용 데이터 수집**
- 지연 P95 / 에러율 / VRAM 사용률
- `max-model-len`/`gpu-memory-utilization`/`max-num-seqs` 조정
- 변경 전후 Δ 비교 → 효과 있으면 스크립트 반영

### **AB 테스트 방법**
```bash
# A 설정 (현재)
--max-model-len 6144 --gpu-memory-utilization 0.82

# B 설정 (테스트)
--max-model-len 4096 --gpu-memory-utilization 0.85

# 성능 비교 후 최적 설정 선택
```

## 🎯 **운영 체크리스트**

### ✅ **일일 점검**
- [ ] `./health-check-60s.sh` 실행
- [ ] GPU 메모리 사용률 확인 (< 90%)
- [ ] 응답 시간 확인 (< 100ms)

### ✅ **주간 점검**
- [ ] `./smoke-test.sh` 실행
- [ ] 에러 로그 분석
- [ ] 성능 메트릭 수집

### ✅ **월간 점검**
- [ ] 모델 성능 평가
- [ ] 확장 필요성 검토
- [ ] 비용 최적화 검토

---

**💡 현재 설정으로 5090 단일로도 놀라울 만큼 탄탄합니다!** 🚀
