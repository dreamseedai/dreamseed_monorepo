# 🚀 DreamSeed AI 운영 가이드

## 📋 현재 상태
- **모델**: Mistral-7B-Instruct v0.3 @8000 ✅
- **GPU**: RTX 5090 (8-11GB / 32,607MB, 25-35%) ✅
- **응답시간**: 평균 20ms ✅
- **성공률**: 100% ✅

## ⏱️ 60초 점검 루틴

### 🔍 **문제 발생 시 즉시 실행**
```bash
# 전체 시스템 점검
./health-check-60s.sh

# 부하 스모크 테스트
./smoke-test.sh

# 상세 진단 (컨테이너 종료 시)
./diagnose-issues.sh
```

**포함 내용:**
1. GPU/메모리 상태
2. vLLM 컨테이너 로그 (최근 20줄)
3. 헬스 체크 (모델 API + 채팅 테스트)
4. 시스템 로그 (OOM/에러 확인)
5. 포트 상태

### 🧪 **부하 테스트**
```bash
./smoke-test.sh
```

**5회 연속 ping으로 에러율/지연 확인**

## 🚨 자주 보이는 종료 원인

### 1. **OOM (Out of Memory)**
- **증상**: 컨테이너 갑자기 종료
- **해결**: `--max-model-len` 낮추기, `--gpu-memory-utilization 0.80~0.85`

### 2. **HF 다운로드 실패**
- **증상**: 모델 로딩 실패, 403/404 에러
- **해결**: 토큰/네트워크 확인, 캐시 볼륨 유지

### 3. **권한/포트 문제**
- **증상**: 포트 바인딩 실패
- **해결**: 포트 변경/권한 확인

## 📈 추천 운영 파라미터 (32GB, 8B 단독)

### 현재 적용된 설정 (최적화됨)
```bash
--dtype auto                    # FP8/FP16 자동 선택
--max-model-len 6144           # 성능/안정성 밸런스
--max-num-seqs 16              # 동시 처리 수
--max-num-batched-tokens 2048  # 토큰 배치 상한
--gpu-memory-utilization 0.82  # 안정 여유
--env HF_HOME=/root/.cache/huggingface  # 캐시 최적화
--shm-size=2g                  # 공유 메모리 확보
```

### 확장 시 권장 설정
```bash
--max-model-len: 4096~6144
--gpu-memory-utilization: 0.82~0.86
```

### 캐시 볼륨 (필수)
```bash
-v $HOME/.cache/huggingface:/root/.cache/huggingface
```

## 🧩 확장 스텝 (필요해질 때)

### 1. **프로필 O: 코딩 7B 온디맨드**
```bash
# 8B가 실행 중일 때 7B 추가
./quick-start-7b.sh

# 7B만 정지 (8B는 계속 실행)
docker stop dreamseed-qwen-7b
```

### 2. **RAG: 임베딩 + pgvector/FAISS**
- DreamSeedAI 지식 정답률 업그레이드
- 벡터 검색으로 컨텍스트 향상

### 3. **70B 업그레이드: Lambda 2×A100 80GB**
- 라우터 `general70` 조건부 분기
- 원격 70B로 성능 향상

## 🎯 운영 체크리스트

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

## 🔧 문제 해결 명령어

### 컨테이너 재시작
```bash
./stop-profile-s.sh
./start-profile-s.sh
```

### 로그 확인
```bash
docker logs dreamseed-llama-8b --tail 100
```

### GPU 상태 확인
```bash
nvidia-smi
```

### 포트 확인
```bash
netstat -tlnp | grep 8000
```

---

**💡 첫 주간 운영 데이터를 모아 보시고—응답 지연/에러율/메모리 곡선을 보내 주시면, 거기에 맞춰 다음 튜닝 한 줄로 이어가겠습니다!** 🚀
