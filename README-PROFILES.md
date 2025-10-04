# 🚀 DreamSeed AI 프로필 가이드

## 📋 프로필 개요

### 🟢 프로필 S (가장 안정) - 단일 7B 상주
- **모델**: Mistral-7B-Instruct v0.3 @8000 (가용 모델)
- **전략**: 가장 간단하고 안정적, 운영 시작/안착에 최적
- **메모리**: ~8-11GB (25-35% 사용률)
- **장점**: 폴백 로직으로 8001/8002 미기동 시에도 안전

### 🔵 프로필 O (권장) - 온디맨드 7B 부팅
- **기본**: Mistral-7B-Instruct v0.3 @8000
- **추가**: Qwen2.5-Coder-7B-Instruct @8001 (필요시)
- **전략**: 필요할 때만 성능 향상, VRAM 부족/복잡도 없음
- **장점**: 코딩 요청↑ 시에만 7B 컨테이너 추가

### 🟡 프로필 D (동시 상주) - 8B + 7B(양자화)
- **조건**: AWQ 변환 모델 필요
- **전략**: 32GB에서 2개 모델 동시 운영
- **주의**: 품질·자원 타협 필요

## 🛠️ 사용법

### 프로필 S (단일 8B)
```bash
# 시작
./start-profile-s.sh

# 테스트
./test-profile-s.sh

# 정지
./stop-profile-s.sh
```

### 프로필 O (온디맨드 7B)
```bash
# 시작 (8B + 7B)
./start-profile-o.sh

# 7B만 빠른 시작 (8B가 이미 실행 중일 때)
./quick-start-7b.sh

# 7B만 정지
docker stop dreamseed-qwen-7b

# 전체 정지
./stop-profile-o.sh
```

## 📊 현재 상태

### GPU 메모리 사용률
- **RTX 5090**: 8-11GB / 32,607MB (25-35%)
- **여유 공간**: ~21-24GB (65-75%)
- **현재 모델**: Mistral-7B-Instruct v0.3 (가용 모델)

### 엔드포인트
- **7B 일반**: http://127.0.0.1:8000 (Mistral-7B-Instruct v0.3)
- **7B 코딩**: http://127.0.0.1:8001 (Qwen2.5-Coder-7B-Instruct)
- **라우터**: http://127.0.0.1:8010

## 🔧 튜닝 팁

### 메모리 최적화 (현재 적용됨)
```bash
# 현재 설정 (안정성 우선)
--max-model-len 6144
--gpu-memory-utilization 0.85

# 32GB에서 여유 부족 시
--max-model-len 4096~6144
--gpu-memory-utilization 0.80~0.85

# 동시 상주 시 (프로필 D)
--gpu-memory-utilization 0.45~0.5 (각각)
```

### 성능 최적화
- **웜업**: 시작 직후 `/v1/models` 1회 호출
- **캐시**: `-v $HOME/.cache/huggingface:/root/.cache/huggingface` 필수
- **공유 메모리**: `--shm-size=2g` 권장

## 🧪 헬스체크

### ⏱️ 60초 점검 루틴 (권장)
```bash
# 전체 시스템 점검
./health-check-60s.sh

# 부하 스모크 테스트
./smoke-test.sh
```

### 문제 진단 (수동)
```bash
# GPU 상태
nvidia-smi

# Docker GPU 지원
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi

# 모델 응답
curl -i http://127.0.0.1:8000/v1/models

# 컨테이너 로그
docker logs $(docker ps -q --filter ancestor=vllm/vllm-openai:latest) --tail 200
```

## 🎯 추천 전략

1. **시작**: 프로필 S (8B 단독)로 안정 운영
2. **확장**: 코딩 요청↑ 시 프로필 O (온디맨드 7B)
3. **고급**: AWQ 모델 있을 때만 프로필 D (동시 상주)
4. **미래**: 품질 한계 시 Lambda Cloud 70B로 확장

## 🔄 70B 전환 준비

8B → 70B 전환 시점:
1. Lambda Cloud 2×A100 80GB 설정
2. `general70` 백엔드를 원격 70B로 추가
3. 라우터에서 조건부 분기 로직 추가
4. 기존 8B는 `general8`로 유지 (폴백용)

---

**💡 현재 권장**: 프로필 S로 시작하여 안정성을 확보한 후, 필요에 따라 프로필 O로 확장
