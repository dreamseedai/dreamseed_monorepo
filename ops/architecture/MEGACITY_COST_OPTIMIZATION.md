# 💰 DreamSeedAI MegaCity – Cost Optimization Guide

## AI · GPU · LLM · Storage · Network 비용을 70% 절감하는 실전 전략

**버전:** 1.0  
**작성일:** 2025-11-22  
**작성자:** DreamSeedAI FinOps & Architecture Team

---

# 📌 0. 개요 (Overview)

DreamSeedAI MegaCity는 **9개 Zone + AI Cluster + Multi-modal 서비스 + GPU 기반 AI** 로 구성된 대규모 플랫폼입니다.

따라서 운영 비용이 효과적으로 관리되지 않으면:

* **GPU 비용 폭증** (vLLM, Whisper, PoseNet)
* **Storage 과다 과금** (K-Zone 미디어, AI 출력물)
* **LLM 호출비 증가** (불필요한 대형 모델 사용)
* **CDN/Traffic 비용 증가** (캐시 미활용)
* **API 서버 과할당 문제** (리소스 낭비)

본 문서는 MegaCity 전체 비용을 **최대 70% 절감**할 수 있는 구조적 FinOps 전략을 제공합니다.

## 문서 목적

- MegaCity 전체 비용 구조 분석
- 5대 비용 영역별 최적화 전략 제시
- GPU/LLM/Storage/Network/Compute 비용 절감 방법
- 실행 가능한 시나리오 및 ROI 계산
- FinOps 모니터링 대시보드 구성

---

# 🧱 1. 비용 구조 요약 (Cost Structure Breakdown)

## 1.1 MegaCity 월간 비용 구조 (예상)

| 비용 항목 | 비중 | 월 예상 비용 (10K 사용자) | 최적화 후 |
|----------|------|---------------------------|----------|
| **GPU 비용** (vLLM, Whisper, PoseNet) | 40~60% | $8,000 ~ $12,000 | $2,400 ~ $4,800 (60~70% 절감) |
| **Cloud Storage / CDN** | 15~25% | $3,000 ~ $5,000 | $900 ~ $1,500 (70% 절감) |
| **Compute** (API, Next.js) | 10~20% | $2,000 ~ $4,000 | $1,200 ~ $2,400 (40% 절감) |
| **Network Traffic** (Egress) | 5~10% | $1,000 ~ $2,000 | $200 ~ $400 (80% 절감) |
| **Monitoring/Logs** | 5% | $1,000 | $500 (50% 절감) |
| **Total** | 100% | **$15,000 ~ $24,000** | **$4,700 ~ $9,600** |

**절감 효과: 60~70% 비용 절감**

## 1.2 비용 최적화 5대 전략

```
┌─────────────────────────────────────────────────────────┐
│  1. GPU 비용 최적화 (40~70% 절감)                       │
│     • 로컬 GPU (RTX 5090) vs Cloud GPU (A100)           │
│     • Auto-scaling (Off-peak shutdown)                  │
│     • Quantization (8bit/4bit)                          │
│     • KV Cache 재사용                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  2. LLM 비용 최적화 (50~85% 절감)                       │
│     • 모델 크기별 역할 분리 (7B/32B/70B)                │
│     • Prompt Compression (토큰 수 50% 감소)             │
│     • vLLM Cache 재사용                                 │
│     • Hybrid Model Routing                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  3. Storage 비용 최적화 (40~85% 절감)                   │
│     • Cloudflare R2 (Egress 무료)                       │
│     • Backblaze B2 Archive (Cold Storage)               │
│     • 미사용 AI 출력물 자동 삭제                         │
│     • Media Compression (WebP, 720p)                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  4. Network 비용 최적화 (50~90% 절감)                   │
│     • Cloudflare CDN 캐시율 90%+ 목표                   │
│     • HTTP/3 + Brotli 압축                              │
│     • 이미지 지연 로딩 (Lazy Loading)                   │
│     • 로그/메트릭 샘플링                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  5. Compute 비용 최적화 (30~50% 절감)                   │
│     • 서버 수 적정화 (Horizontal Scaling)               │
│     • FastAPI 최적화 (Worker, Connection pooling)       │
│     • Next.js ISR (Incremental Static Regeneration)     │
│     • Nginx/Traefik 압축·캐시 최대화                    │
└─────────────────────────────────────────────────────────┘
```

---

# 🔥 2. GPU 비용 최적화 (절감 효과: 40%~70%)

AI 비용은 대부분 GPU에서 발생합니다. DreamSeedAI는 **로컬 GPU + Edge GPU + Spot GPU** 혼합 구조를 사용합니다.

## 2.1 RTX 5090 (로컬) vs A100 (Cloud) 비용 비교

### 비용 비교 (시간당)

| GPU | 시간당 비용 | 월 비용 (24/7) | 연 비용 |
|-----|-------------|----------------|---------|
| **AWS A100 (80GB)** | $4.00/hr | $2,880 | $34,560 |
| **GCP A100 (40GB)** | $3.40/hr | $2,448 | $29,376 |
| **RTX 5090 (48GB) 로컬** | $0.20/hr (전기비 포함) | $144 | $1,728 |

**절감 효과: RTX 5090 로컬 GPU → 연간 $27,000~$32,000 절감 (GPU 1대당)**

### ROI 계산

```
RTX 5090 구매 비용: $2,000 (예상)
월 전기비: $30~$50
투자 회수 기간: 약 2~3개월
```

### 전략

```python
# AI Router 설정
AI_GPU_CONFIG = {
    "primary": "local_rtx5090",  # 로컬 GPU 우선
    "fallback": "cloud_a100",    # 과부하 시 Cloud GPU
    "cost_threshold": 0.9        # GPU 사용률 90% 초과 시 Cloud 사용
}
```

---

## 2.2 GPU Auto-scaling (Off-peak Shutdown)

### 시간대별 사용 패턴 분석

```
Peak 시간대 (09:00~22:00): GPU 사용률 70~90%
Off-peak (23:00~08:00): GPU 사용률 5~15%
```

### Auto-scaling 전략

```python
import schedule
from datetime import datetime

def check_gpu_scale():
    hour = datetime.now().hour
    
    if 9 <= hour <= 22:  # Peak
        target_gpu_count = 2
    else:  # Off-peak
        target_gpu_count = 1
    
    current_gpu_count = get_active_gpu_count()
    
    if target_gpu_count > current_gpu_count:
        scale_up_gpu(target_gpu_count - current_gpu_count)
    elif target_gpu_count < current_gpu_count:
        scale_down_gpu(current_gpu_count - target_gpu_count)

# 매 시간마다 체크
schedule.every(1).hours.do(check_gpu_scale)
```

**절감 효과: Off-peak GPU 1대 감축 → 월 $1,440 절감 (A100 기준)**

---

## 2.3 vLLM Key/Value Cache (KV Cache) 재사용

### KV Cache란?

LLM은 이전 토큰의 Key/Value를 재사용하여 추론 속도를 높입니다.

### 최적화 설정

```python
# vLLM 서버 실행
vllm serve Qwen/Qwen2.5-32B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \  # KV Cache 활성화
  --max-num-seqs 64 \
  --dtype bfloat16
```

### 효과

- **처리량 증가**: 20~30% 더 많은 요청 처리
- **Latency 감소**: 평균 응답 시간 30% 감소
- **GPU 효율**: 동일 GPU로 더 많은 사용자 지원

**절감 효과: GPU 1대로 1.3배 처리량 → GPU 1대 절감 = 월 $2,448 절감**

---

## 2.4 Quantization (8bit/4bit) 적용

### Quantization이란?

모델 가중치를 FP16 → INT8 또는 INT4로 변환하여 메모리 사용량 감소.

### 비교

| Precision | 메모리 사용량 (70B 모델) | Inference 속도 | 정확도 |
|-----------|--------------------------|----------------|--------|
| **FP16** | 140GB | 기준 | 100% |
| **INT8 (GPTQ)** | 70GB | 1.5x | 99.5% |
| **INT4 (AWQ)** | 35GB | 2x | 98% |

### 적용 예시

```python
# GPTQ 8bit 모델 로딩
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-32B-Instruct-GPTQ-Int8",
    device_map="auto",
    trust_remote_code=True
)
```

**절감 효과: 메모리 50% 감소 → GPU 1대로 2배 모델 크기 서빙 가능**

---

## 2.5 Multi-GPU Parallelism 최적화

### Tensor Parallelism (TP) 비용

```
TP=1: GPU 1대, 처리량 100%
TP=2: GPU 2대, 처리량 150% (2배 비용, 1.5배 성능)
TP=4: GPU 4대, 처리량 200% (4배 비용, 2배 성능)
```

### 전략

```python
# 작은 모델은 TP=1 사용
SMALL_MODELS = ["7B", "14B"]  # TP=1
MEDIUM_MODELS = ["32B"]       # TP=2
LARGE_MODELS = ["70B"]        # TP=4

def select_tensor_parallel(model_size: str) -> int:
    if model_size in SMALL_MODELS:
        return 1
    elif model_size in MEDIUM_MODELS:
        return 2
    else:
        return 4
```

**절감 효과: 작은 모델에 TP=1 사용 → GPU 1대 절감 = 월 $2,448**

---

## 2.6 GPU 비용 최적화 체크리스트

```
□ RTX 5090 로컬 GPU 우선 사용
□ Off-peak 시간대 GPU 1대로 축소
□ vLLM KV Cache 활성화
□ GPTQ/AWQ Quantization 적용
□ TP=1로 작은 모델 서빙
□ GPU 사용률 70~90% 유지 (< 70% → scale down)
□ Cloud GPU는 Spot Instance 사용 (70% 할인)
```

---

# 🧠 3. LLM 비용 최적화 (절감 효과: 50%~85%)

LLM 비용은 **모델 선택, 프롬프트 구성, 캐싱 전략**에 따라 천차만별입니다.

## 3.1 모델 크기별 역할 분리

### 모델 역할 매트릭스

| 모델 크기 | 용도 | Latency | 비용 (상대) | 사용 비중 목표 |
|----------|------|---------|-------------|---------------|
| **7B** (Small) | 간단한 Q/A, 필터링, 분류 | < 1s | 1x | 50~60% |
| **14B~32B** (Medium) | 교육 분석, Essay feedback | < 2s | 3x | 30~40% |
| **70B+** (Large) | 최상위 품질 필요 시 | < 5s | 10x | 5~10% |

### Routing 전략

```python
def select_model(task_type: str, user_tier: str) -> str:
    # Simple tasks → Small model
    if task_type in ["classification", "qa", "filter"]:
        return "Qwen2.5-7B"
    
    # Educational analysis → Medium model
    elif task_type in ["essay_feedback", "math_tutor"]:
        if user_tier == "pro":
            return "Qwen2.5-32B"
        else:
            return "Qwen2.5-14B"
    
    # Premium features → Large model
    elif task_type in ["advanced_reasoning", "code_review"]:
        if user_tier == "pro":
            return "Qwen2.5-72B"
        else:
            return "Qwen2.5-32B"  # Fallback
    
    return "Qwen2.5-7B"  # Default
```

**절감 효과: 대형 모델 사용 50% 감소 → 월 $3,000~$5,000 절감**

---

## 3.2 Prompt Compression (프롬프트 길이 50% 감소)

### 문제점

```python
# Bad: 불필요하게 긴 프롬프트 (500 tokens)
prompt = f"""
You are an AI tutor helping students with math problems.
The student is in grade 10 and studying algebra.
Please provide a detailed explanation with step-by-step solutions.

Question: {user_question}

Please be encouraging and supportive.
Use simple language that a 10th grader can understand.
Include examples if needed.
"""
```

### 최적화

```python
# Good: 간결한 프롬프트 (150 tokens)
prompt = f"""Math Tutor (Grade 10):
Q: {user_question}
Explain step-by-step, simple language."""
```

### System Prompt 재사용

```python
# System prompt는 한 번만 전송
SYSTEM_PROMPTS = {
    "math_tutor": "You are a helpful math tutor for grade 10 students. Explain step-by-step.",
    "essay_feedback": "Provide constructive essay feedback focusing on structure and clarity."
}

# API 호출 시
response = llm.generate(
    system=SYSTEM_PROMPTS["math_tutor"],
    user=user_question  # 짧게 유지
)
```

**절감 효과: 프롬프트 50% 단축 → 토큰 비용 50% 절감**

---

## 3.3 vLLM 내부 Cache 활용

### Prefix Caching

```python
# 동일한 system prompt는 캐시됨
responses = []
for question in user_questions:
    response = llm.generate(
        system="You are a helpful math tutor.",  # 캐시됨
        user=question
    )
    responses.append(response)

# 첫 요청: 500ms
# 이후 요청: 100ms (80% 빠름)
```

### 효과

- **Cache Hit Rate**: 60~80%
- **Latency 감소**: 50~70%
- **처리량 증가**: 2~3배

**절감 효과: GPU 사용 시간 50% 감소 → 월 $1,200~$2,400 절감**

---

## 3.4 Hybrid Model Routing (언어별/도메인별)

### 언어별 모델 선택

```python
LANGUAGE_MODELS = {
    "ko": "beomi/Llama-3-Open-Ko-8B",     # 한국어 특화 (저렴)
    "en": "Qwen2.5-7B-Instruct",          # 영어 범용
    "ja": "elyza/Llama-3-ELYZA-JP-8B",    # 일본어 특화
    "zh": "Qwen2.5-7B-Instruct"           # 중국어 (Qwen 기본 강점)
}

def select_language_model(text: str) -> str:
    lang = detect_language(text)
    return LANGUAGE_MODELS.get(lang, "Qwen2.5-7B-Instruct")
```

### 도메인별 모델 선택

```python
DOMAIN_MODELS = {
    "math": "deepseek-ai/deepseek-math-7b",  # 수학 특화
    "code": "deepseek-ai/deepseek-coder-6.7b",  # 코딩 특화
    "general": "Qwen2.5-7B-Instruct"  # 범용
}
```

**절감 효과: 특화 모델 사용 → 대형 모델 대비 70% 비용 절감**

---

## 3.5 Response Caching (Redis)

### 동일 질문 캐싱

```python
import hashlib
import redis

r = redis.Redis()

def get_llm_response(prompt: str) -> str:
    # 프롬프트 해시
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    
    # 캐시 확인
    cached = r.get(f"llm:{prompt_hash}")
    if cached:
        return cached.decode()
    
    # LLM 호출
    response = llm.generate(prompt)
    
    # 캐시 저장 (24시간)
    r.setex(f"llm:{prompt_hash}", 86400, response)
    
    return response
```

**절감 효과: Cache Hit Rate 30% → LLM 호출 30% 감소 → 월 $900~$1,500 절감**

---

## 3.6 LLM 비용 최적화 체크리스트

```
□ 작은 모델(7B) 사용 비중 50% 이상
□ 대형 모델(70B) 사용 비중 10% 이하
□ Prompt 길이 최소화 (< 200 tokens)
□ System prompt 재사용
□ vLLM Prefix Caching 활성화
□ 언어별/도메인별 특화 모델 사용
□ Response Caching (Redis) 구현
□ 동일 질문 Cache Hit Rate 30% 이상
```

---

# 📦 4. Storage 비용 최적화 (절감 효과: 40%~85%)

MegaCity는 미디어(K-Zone), 문제은행, AI 출력물이 많아 Storage 비용이 급증할 수 있습니다.

## 4.1 Cloudflare R2 (Egress 무료) 필수 사용

### 비용 비교

| Storage | 저장 비용 | Egress 비용 | 월 비용 (1TB 저장, 10TB 전송) |
|---------|----------|-------------|------------------------------|
| **AWS S3** | $0.023/GB | $0.09/GB | $23 + $900 = **$923** |
| **GCS** | $0.020/GB | $0.12/GB | $20 + $1,200 = **$1,220** |
| **Cloudflare R2** | $0.015/GB | **$0** | $15 + $0 = **$15** |

**절감 효과: R2 사용 → 월 $900~$1,200 절감 (1TB 저장, 10TB 전송 기준)**

### 마이그레이션 전략

```bash
# S3 → R2 마이그레이션
rclone sync s3:dreamseed-storage r2:dreamseed-storage \
  --progress \
  --transfers 8 \
  --checkers 16
```

### R2 사용 예시

```python
import boto3

# R2 연결 (S3 호환 API)
s3 = boto3.client(
    's3',
    endpoint_url='https://<account_id>.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

# 파일 업로드
s3.upload_file('local.mp4', 'dreamseed-storage', 'kzone/video.mp4')
```

---

## 4.2 Backblaze B2 Archive (Cold Storage)

### 사용 전략

```
Hot Data (30일 이내): R2 (자주 접근)
Warm Data (30~90일): R2 (가끔 접근)
Cold Data (90일+): B2 (거의 접근 안 함)
```

### 비용 비교

| Storage | 저장 비용 | Egress 비용 (첫 1GB 무료 후) |
|---------|----------|------------------------------|
| **R2** | $0.015/GB | $0 |
| **B2** | $0.005/GB | $0.01/GB |

**절감 효과: Cold Storage B2 이동 → 저장 비용 67% 절감**

### 자동 아카이빙

```python
import boto3
from datetime import datetime, timedelta

def archive_old_files():
    # R2에서 90일 이상 파일 찾기
    cutoff_date = datetime.now() - timedelta(days=90)
    
    for obj in s3_r2.list_objects_v2(Bucket='dreamseed-storage')['Contents']:
        if obj['LastModified'] < cutoff_date:
            # B2로 복사
            s3_b2.copy_object(
                CopySource={'Bucket': 'dreamseed-storage', 'Key': obj['Key']},
                Bucket='dreamseed-archive',
                Key=obj['Key']
            )
            
            # R2에서 삭제
            s3_r2.delete_object(Bucket='dreamseed-storage', Key=obj['Key'])
```

---

## 4.3 미사용 AI 출력물 자동 삭제 정책

### 임시 파일 수명 정책

```python
RETENTION_POLICIES = {
    "/kzone/tmp/*": 24,          # 24시간
    "/tmp/whisper/*": 7,         # 7일
    "/tmp/posenet/*": 7,         # 7일
    "/exams/attempts/*/audio": 30,  # 30일
    "/ai-outputs/temp/*": 3      # 3일
}

def cleanup_expired_files():
    for prefix, retention_days in RETENTION_POLICIES.items():
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        for obj in s3.list_objects_v2(Bucket='dreamseed-storage', Prefix=prefix)['Contents']:
            if obj['LastModified'] < cutoff:
                s3.delete_object(Bucket='dreamseed-storage', Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
```

### Cron Job 설정

```bash
# /etc/cron.daily/cleanup-storage.sh
#!/bin/bash
python /opt/scripts/cleanup_expired_files.py
```

**절감 효과: 임시 파일 자동 삭제 → Storage 20~30% 절감**

---

## 4.4 Media Compression 자동화

### 비디오 압축

```python
import ffmpeg

def compress_video(input_path: str, output_path: str):
    # 1080p → 720p, H.265 인코딩
    ffmpeg.input(input_path).output(
        output_path,
        vcodec='libx265',
        crf=28,
        vf='scale=-2:720',
        acodec='aac',
        audio_bitrate='128k'
    ).run()
```

### 이미지 압축 (WebP)

```python
from PIL import Image

def compress_image(input_path: str, output_path: str):
    img = Image.open(input_path)
    img.save(output_path, 'webp', quality=85, method=6)
```

### 자동 압축 파이프라인

```python
@app.post("/api/v1/kzone/upload")
async def upload_kzone_media(file: UploadFile):
    # 원본 저장
    original_path = f"/tmp/{file.filename}"
    with open(original_path, "wb") as f:
        f.write(await file.read())
    
    # 압축
    compressed_path = f"/tmp/compressed_{file.filename}"
    if file.content_type.startswith("video"):
        compress_video(original_path, compressed_path)
    elif file.content_type.startswith("image"):
        compress_image(original_path, compressed_path)
    
    # R2 업로드
    s3.upload_file(compressed_path, 'dreamseed-storage', f'kzone/{file.filename}')
    
    # 로컬 임시 파일 삭제
    os.remove(original_path)
    os.remove(compressed_path)
    
    return {"status": "uploaded", "size_reduction": "40%"}
```

**절감 효과: 비디오/이미지 압축 → Storage 40~60% 절감**

---

## 4.5 Storage 비용 최적화 체크리스트

```
□ Cloudflare R2로 전체 마이그레이션 (Egress 무료)
□ Cold Storage는 B2로 이동 (90일+)
□ 임시 파일 자동 삭제 정책 적용
□ 비디오 720p + H.265 압축
□ 이미지 WebP 변환 (Quality 85)
□ 중복 파일 제거 (Deduplication)
□ Storage 사용량 모니터링 (Grafana Dashboard)
```

---

# 🌐 5. Network 비용 최적화 (절감 효과: 50%~90%)

Network 비용은 주로 **Egress (데이터 전송)** 에서 발생합니다.

## 5.1 Cloudflare CDN 캐시율 90% 이상 목표

### 캐시 가능한 리소스

```
정적 파일: CSS, JS, Fonts
미디어: 이미지, 비디오, 오디오
K-Zone 콘텐츠: 댄스 영상, 음성 파일
API 응답 (선택적): 문제은행 목록, 공지사항
```

### Cloudflare Cache Rule 설정

```javascript
// Cloudflare Page Rules
{
  "url": "https://cdn.dreamseedai.com/*",
  "cache_level": "cache_everything",
  "edge_cache_ttl": 2592000  // 30일
}

{
  "url": "https://api.dreamseedai.com/api/v1/questions*",
  "cache_level": "cache_everything",
  "edge_cache_ttl": 3600  // 1시간
}
```

### Cache Control 헤더

```python
@app.get("/api/v1/questions")
async def get_questions(response: Response):
    questions = await db.fetch_all("SELECT * FROM questions")
    
    # 1시간 캐시
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return questions
```

**절감 효과: Cache Hit Rate 90% → Origin 트래픽 90% 감소**

---

## 5.2 HTTP/3 + Brotli 압축

### HTTP/3 활성화

```nginx
# Nginx HTTP/3 설정
listen 443 quic reuseport;
listen 443 ssl http2;

ssl_protocols TLSv1.3;
http3 on;
quic_retry on;

add_header Alt-Svc 'h3=":443"; ma=86400';
```

### Brotli 압축

```nginx
# Brotli compression
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css text/xml text/javascript application/json application/javascript;
```

### 효과

- **HTTP/3**: 패킷 손실 감소, 전송 속도 20% 향상
- **Brotli**: Gzip 대비 20~30% 더 압축

**절감 효과: 전송량 30~40% 감소 → Network 비용 30~40% 절감**

---

## 5.3 이미지 지연 로딩 (Lazy Loading)

### Next.js Image Component

```tsx
import Image from 'next/image'

export function KZoneGallery({ videos }) {
  return (
    <div>
      {videos.map(video => (
        <Image
          src={video.thumbnail}
          width={320}
          height={180}
          loading="lazy"  // 지연 로딩
          placeholder="blur"
          alt={video.title}
        />
      ))}
    </div>
  )
}
```

### 효과

- 초기 페이지 로딩 시 이미지 전송량 70% 감소
- 사용자가 스크롤해야만 이미지 로드

**절감 효과: 페이지뷰당 전송량 50% 감소**

---

## 5.4 로그/메트릭 샘플링

### 문제점

```
대량 트래픽 시 모든 요청 로깅 → 로그 전송량 급증
예: 100K req/day → 10GB 로그/day
```

### 샘플링 전략

```python
import random

@app.middleware("http")
async def log_sampling_middleware(request: Request, call_next):
    # 1% 샘플링
    if random.random() < 0.01:
        log_request(request)
    
    response = await call_next(request)
    return response
```

### Prometheus 샘플링

```yaml
# Prometheus scrape config
scrape_configs:
  - job_name: 'backend-api'
    scrape_interval: 30s  # 15s → 30s로 증가
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'http_request_.*'
        action: drop  # 불필요한 메트릭 제거
```

**절감 효과: 로그/메트릭 전송량 90% 감소**

---

## 5.5 Network 비용 최적화 체크리스트

```
□ Cloudflare CDN Cache Hit Rate > 90%
□ HTTP/3 활성화
□ Brotli 압축 적용
□ 이미지 Lazy Loading 구현
□ 로그 샘플링 (1~5%)
□ API 응답 Gzip 압축
□ WebSocket 메시지 압축
□ Static assets는 CDN에서 100% 제공
```

---

# 🖥️ 6. Compute 비용 최적화 (절감 효과: 30%~50%)

## 6.1 서버 수 적정화 (Horizontal Scaling)

### 과할당 문제

```
현재: API 서버 5대 (각 8 vCPU, 16GB RAM)
평균 CPU 사용률: 20%
→ 3대로 충분
```

### 적정화 전략

```python
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # 70% CPU 목표
```

**절감 효과: 서버 2대 감축 → 월 $400~$800 절감**

---

## 6.2 FastAPI 최적화

### uvicorn Worker 수 조절

```python
# 과할당
uvicorn main:app --workers 16  # CPU 8개인데 16 workers

# 적정
uvicorn main:app --workers 8  # CPU 개수만큼
```

### DB Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,        # 기본 연결 수
    max_overflow=20,     # 추가 연결 수
    pool_pre_ping=True,  # 연결 검증
    pool_recycle=3600    # 1시간마다 재연결
)
```

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="api-cache")

@app.get("/api/v1/questions")
@cache(expire=3600)  # 1시간 캐시
async def get_questions():
    return await db.fetch_all("SELECT * FROM questions")
```

**절감 효과: CPU 사용률 30% 감소 → 서버 1대 절감**

---

## 6.3 Next.js 최적화

### ISR (Incremental Static Regeneration)

```tsx
// pages/questions/[id].tsx
export async function getStaticProps({ params }) {
  const question = await fetchQuestion(params.id)
  
  return {
    props: { question },
    revalidate: 3600  // 1시간마다 재생성
  }
}

export async function getStaticPaths() {
  return {
    paths: [],
    fallback: 'blocking'  // 첫 요청 시 생성
  }
}
```

### Edge Functions (Cloudflare Workers)

```typescript
// Cloudflare Workers
export default {
  async fetch(request: Request) {
    // API 요청을 Edge에서 처리
    const url = new URL(request.url)
    
    if (url.pathname.startsWith('/api/public/')) {
      // Edge에서 직접 응답
      return new Response(JSON.stringify({ data: "..." }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }
    
    // Origin으로 전달
    return fetch(request)
  }
}
```

**절감 효과: Origin 요청 50% 감소 → Compute 비용 30% 절감**

---

## 6.4 Nginx/Traefik 압축·캐시 최대화

### Nginx 정적 파일 캐시

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

### Gzip 압축

```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
```

**절감 효과: 정적 파일 Origin hit < 10%**

---

## 6.5 Compute 비용 최적화 체크리스트

```
□ API 서버 CPU 사용률 60~80% 유지
□ uvicorn workers = CPU 개수
□ DB Connection Pooling 구성
□ FastAPI Response Caching (Redis)
□ Next.js ISR 활성화
□ Edge Functions로 간단한 API 처리
□ Nginx 정적 파일 캐시 30일
□ Gzip/Brotli 압축 활성화
```

---

# 🔁 7. Observability 기반 비용 절감

## 7.1 Prometheus 기반 비용 경고

### Cost Alerts

```yaml
groups:
  - name: cost_alerts
    rules:
      - alert: LowGPUUtilization
        expr: nvidia_gpu_utilization < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "GPU utilization < 30% for 1 hour"
          action: "Consider scaling down GPU"
      
      - alert: HighStorageGrowth
        expr: rate(storage_used_bytes[1d]) > 10GB
        for: 1d
        labels:
          severity: warning
        annotations:
          summary: "Storage growing > 10GB/day"
          action: "Check for temporary files"
      
      - alert: HighEgressCost
        expr: rate(network_egress_bytes[1d]) > 1TB
        for: 1d
        labels:
          severity: critical
        annotations:
          summary: "Network egress > 1TB/day"
          action: "Check CDN cache hit rate"
```

---

## 7.2 Grafana 비용 대시보드

### Dashboard 구성

```
1. GPU 비용 추이 (시간별, 일별, 월별)
2. LLM 모델별 비용 (7B/32B/70B)
3. Storage 사용량 및 증가율
4. Network Egress 비용
5. Compute 비용 (API/Frontend)
6. 총 비용 대시보드
```

### Cost per User Metric

```python
from prometheus_client import Gauge

cost_per_user = Gauge('cost_per_user_dollars', 'Cost per active user')

@app.on_event("startup")
@repeat_every(seconds=3600)  # 1시간마다
async def calculate_cost_per_user():
    total_cost = await get_total_monthly_cost()  # FinOps API
    active_users = await db.scalar("SELECT count(*) FROM users WHERE last_active > NOW() - INTERVAL '30 days'")
    
    cost_per_user.set(total_cost / active_users)
```

---

## 7.3 Loki 로그 절감

### 로그 Retention 정책

```yaml
# Loki config
retention_enabled: true
retention_period: 30d  # 30일 후 삭제

# 우선순위별 보관 기간
limits_config:
  retention_stream:
    - selector: '{level="error"}'
      priority: 1
      period: 90d  # 에러 로그는 90일
    - selector: '{level="info"}'
      priority: 2
      period: 30d  # 일반 로그는 30일
    - selector: '{level="debug"}'
      priority: 3
      period: 7d   # 디버그 로그는 7일
```

**절감 효과: 로그 저장 비용 50% 절감**

---

# 🧮 8. 실행 가능한 비용 최적화 시나리오 (실전)

## 시나리오 A — GPU 비용 60% 절감

### 현재 상태

```
GPU: A100 × 2대 (24/7 운영)
월 비용: $5,760
```

### 최적화 전략

1. **RTX 5090 로컬 GPU 도입** (1대)
   - 비용: $2,000 (초기 투자)
   - 월 전기비: $50
   
2. **Off-peak GPU 1대로 축소** (23:00~08:00)
   - 절감: $1,440/월
   
3. **vLLM KV Cache 활성화**
   - 처리량 30% 증가 → GPU 1대로 충분
   
4. **GPTQ 8bit 모델 사용**
   - 메모리 50% 감소 → 더 큰 모델 서빙 가능

### 최적화 후

```
GPU: RTX 5090 × 1대 + A100 × 1대 (Peak only)
월 비용: $50 (전기) + $1,440 (A100 12h/day) = $1,490
절감: $4,270/월 (74% 절감)
```

**ROI: 2개월 내 투자 회수**

---

## 시나리오 B — Storage 비용 70% 절감

### 현재 상태

```
Storage: AWS S3 (1TB)
Egress: 10TB/월
월 비용: $23 (저장) + $900 (Egress) = $923
```

### 최적화 전략

1. **Cloudflare R2로 마이그레이션**
   - Egress 무료
   
2. **비디오 720p + H.265 압축**
   - 파일 크기 50% 감소
   
3. **임시 파일 자동 삭제** (24시간~7일)
   - Storage 20% 감소
   
4. **Cold Storage B2 이동** (90일+)
   - 저장 비용 67% 감소

### 최적화 후

```
Storage: R2 (400GB) + B2 (600GB Archive)
Egress: $0 (R2 무료)
월 비용: $6 (R2) + $3 (B2) = $9
절감: $914/월 (99% Egress 절감, 총 90% 절감)
```

---

## 시나리오 C — LLM 비용 50% 절감

### 현재 상태

```
LLM 사용:
- 70B 모델: 50% (비용 높음)
- 32B 모델: 30%
- 7B 모델: 20%
월 GPU 비용: $6,000
```

### 최적화 전략

1. **모델 역할 재분배**
   - 7B: 60% (간단한 Q/A, 필터링)
   - 32B: 30% (교육 분석)
   - 70B: 10% (Premium only)
   
2. **Prompt 길이 50% 단축**
   - 토큰 비용 50% 절감
   
3. **Response Caching (Redis)**
   - Cache Hit Rate 30%
   
4. **언어별 특화 모델 사용**
   - 한국어: beomi/Llama-3-Open-Ko-8B (저렴)

### 최적화 후

```
월 GPU 비용: $3,000
절감: $3,000/월 (50% 절감)
```

---

## 시나리오 D — Network 비용 80% 절감

### 현재 상태

```
Network Egress: 10TB/월
CDN Cache Hit Rate: 60%
월 비용: $900 (S3 Egress)
```

### 최적화 전략

1. **Cloudflare CDN Cache Hit Rate 90% 목표**
   - Origin 트래픽 90% 감소
   
2. **R2 사용** (Egress 무료)
   
3. **Brotli 압축**
   - 전송량 30% 감소
   
4. **이미지 Lazy Loading**
   - 초기 로딩 50% 감소

### 최적화 후

```
Network Egress: $0 (R2 무료)
월 비용: $0
절감: $900/월 (100% 절감)
```

---

## 전체 시나리오 요약

| 시나리오 | 현재 비용 | 최적화 후 | 절감액 | 절감률 |
|----------|----------|----------|--------|--------|
| **A: GPU** | $5,760 | $1,490 | $4,270 | 74% |
| **B: Storage** | $923 | $9 | $914 | 99% |
| **C: LLM** | $6,000 | $3,000 | $3,000 | 50% |
| **D: Network** | $900 | $0 | $900 | 100% |
| **Total** | **$13,583** | **$4,499** | **$9,084** | **67%** |

**연간 절감액: $109,008**

---

# 🏁 9. 결론

이 **Cost Optimization Guide**는 DreamSeedAI MegaCity의 운영 비용을 **60~70% 절감**할 수 있는 구조적 FinOps 전략을 제공합니다.

## 핵심 최적화 원칙

1. **GPU: 로컬 우선, Cloud Fallback** (RTX 5090 → 74% 절감)
2. **LLM: 작은 모델 우선, 큰 모델 선택적** (50% 절감)
3. **Storage: R2 + B2 + 압축 + 자동 삭제** (90% 절감)
4. **Network: CDN 90% Cache + R2 Egress 무료** (100% 절감)
5. **Compute: 적정 Scaling + Caching** (40% 절감)

## 실행 우선순위

```
Phase 1 (즉시 적용):
  ✓ R2 마이그레이션 (Egress 무료)
  ✓ 임시 파일 자동 삭제
  ✓ Cloudflare CDN Cache 90%
  
Phase 2 (1개월 내):
  ✓ RTX 5090 로컬 GPU 도입
  ✓ GPTQ 8bit 모델 적용
  ✓ 모델 역할 재분배 (7B 60%)
  
Phase 3 (3개월 내):
  ✓ Off-peak GPU Auto-scaling
  ✓ Response Caching (Redis)
  ✓ 비디오/이미지 자동 압축
```

## FinOps Dashboard

Grafana에서 다음을 모니터링:

```
□ 월간 총 비용 (Target: $5,000 이하)
□ Cost per User (Target: $0.50 이하)
□ GPU Utilization (Target: 70~90%)
□ Storage Growth Rate (Target: < 5GB/day)
□ CDN Cache Hit Rate (Target: > 90%)
□ LLM 모델 분포 (7B: 60%, 32B: 30%, 70B: 10%)
```

---

**문서 완료 - DreamSeedAI MegaCity Cost Optimization Guide v1.0**
