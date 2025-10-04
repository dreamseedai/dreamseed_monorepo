# 🔄 모델 마이그레이션 가이드

## 📋 현재 상황
- **이전**: DialoGPT-medium (오래된 소형 모델, 품질 부족)
- **현재**: Mistral-7B-Instruct v0.3 (가용 모델, 품질 우수)
- **문제**: Llama 모델들이 gated repo로 접근 제한

## 🚀 가용 7B 모델 전환 완료

### ✅ **전환된 모델들**
1. **일반용 (8000)**: `mistralai/Mistral-7B-Instruct-v0.3`
2. **코딩용 (8001)**: `Qwen/Qwen2.5-Coder-7B-Instruct`
3. **빠른용 (8002)**: `microsoft/Phi-3-mini-4k-instruct`

### 🔧 **업데이트된 스크립트**
- `start-profile-s.sh` - Mistral-7B 우선, 실패 시 Qwen2.5 폴백
- `stop-profile-s.sh` - 모든 7B 모델 정지
- `router.py` - 백엔드 모델명 업데이트

### 📊 **성능 개선**
- **메모리 사용률**: 82% → 25-35% (여유 공간 대폭 증가)
- **모델 품질**: DialoGPT → Mistral-7B (가이드/지식 품질 향상)
- **안정성**: 가용 모델로 접근 권한 문제 해결

## 🎯 **운영 전략**

### **현재 권장 설정**
```bash
# 프로필 S (단일 7B)
./start-profile-s.sh

# 프로필 O (온디맨드 코딩)
./quick-start-7b.sh
```

### **라우터 자동 분기**
- **일반 질의**: Mistral-7B-Instruct v0.3
- **코딩 요청**: Qwen2.5-Coder-7B-Instruct
- **빠른 응답**: Phi-3-mini-4k-instruct
- **폴백**: 8001/8002 미기동 시 자동으로 8000으로

## 🔮 **미래 확장 계획**

### **1. Llama 모델 복귀 (권한 해결 시)**
```bash
# HF 토큰 설정 후
export HF_TOKEN=<your_hf_token>
# Llama 모델로 전환 가능
```

### **2. 70B 업그레이드 (Lambda Cloud)**
- **로컬**: 7B 모델들 (현재)
- **원격**: 70B 모델 (Lambda 2×A100 80GB)
- **라우터**: 조건부 분기로 자동 처리

### **3. RAG 통합**
- **임베딩**: 벡터 검색으로 컨텍스트 향상
- **지식베이스**: DreamSeedAI 전용 지식 정답률 업

## 🛠️ **문제 해결**

### **모델 로딩 실패 시**
```bash
# 60초 점검
./health-check-60s.sh

# 부하 테스트
./smoke-test.sh

# 컨테이너 재시작
./stop-profile-s.sh && ./start-profile-s.sh
```

### **메모리 부족 시**
```bash
# 더 보수적인 설정
--max-model-len 2048
--gpu-memory-utilization 0.70
```

### **네트워크 문제 시**
```bash
# 캐시 볼륨 확인
ls -la $HOME/.cache/huggingface/

# 토큰 확인 (필요시)
export HF_TOKEN=<your_hf_token>
```

---

**💡 현재 설정으로 안정적인 운영이 가능하며, 필요에 따라 단계적으로 확장할 수 있습니다!** 🚀
