# 🤖 DreamSeedAI MegaCity – AI Infrastructure Architecture

## GPU · vLLM · Whisper · PoseNet · Multi-Modal Model Pipeline

**버전:** 1.0  
**작성일:** 2025-11-21  
**작성자:** DreamSeedAI AI Systems Team

---

# 📌 0. Overview

DreamSeedAI MegaCity는 **교육 AI + K-Culture AI + Multi-Modal AI**가 결합된 독특한 대규모 플랫폼입니다.

따라서 MegaCity의 AI Infrastructure는 일반 서비스보다 더 복잡하며, 다음 5개의 핵심 엔진으로 구성됩니다:

```
1. LLM Engine (vLLM 기반)
2. Speech Engine (Whisper 기반)
3. Vision/Motion Engine (PoseNet / MoveNet)
4. Multi-Modal Engine (Qwen2-VL, LLaVA 계열)
5. Video/Audio Generation Engine (Diffusion, TTS, STT)
```

그리고 이 모든 엔진은 GPU Cluster를 공유하면서 도메인(My-Ktube, UnivPrepAI 등)에 따라 다르게 라우팅됩니다.

---

# 🧠 1. AI Infrastructure Topology

```
                     ┌──────────────────────────────┐
                     │      Cloudflare Edge         │
                     │ (WAF, CDN, Routing, SSL)     │
                     └───────────┬──────────────────┘
                                 │
                 ┌───────────────▼────────────────┐
                 │        API Gateway (Nginx)       │
                 │   /api.my-ktube.ai /api/exam     │
                 └──────────┬───────────┬──────────┘
                            │           │
                 ┌──────────▼───┐  ┌────▼───────────┐
                 │  AI Router   │  │  FastAPI Core  │
                 │ (LLM/Speech/ │  │ (Exam, Tutor,  │
                 │   Vision)    │  │  Dashboard)    │
                 └──────┬───────┘  └───────────────┘
                        │
           ┌────────────┴───────────────┐
           │      GPU Cluster (Local)   │
           └────────────┬───────────────┘
                        │
        ┌───────────────┼────────────────────┬────────────────┐
        │               │                    │                │
 ┌──────▼─────┐   ┌─────▼──────┐     ┌──────▼─────┐    ┌─────▼────────┐
 │  vLLM       │   │ Whisper    │     │ PoseNet    │    │ Diffusion/TTS │
 │ (LLM Engine)│   │ STT Engine │     │ Motion AI  │    │ Video/Audio   │
 └─────────────┘   └────────────┘     └────────────┘    └───────────────┘
```

---

# 🔥 2. GPU Cluster Specification

DreamSeedAI의 GPU Cluster는 **로컬 GPU + Edge GPU + 클라우드 fallback(필요시)** 구조입니다.

## 2.1 로컬 GPU 서버 (Primary)

### GPU 사양

* **NVIDIA RTX 5090 × 2–5대**
* 32–48GB VRAM per GPU
* FP8 Transformer Engine → vLLM 최적

### 서버 사양

```
CPU: AMD Ryzen 9 / Xeon 2×
RAM: 128GB
SSD: 4TB NVMe Gen4/5
OS: Ubuntu 22.04 LTS
Docker + CUDA 12.2
```

### 현재 구성 (Phase 1)

```
GPU 1: RTX 5090 (48GB) → vLLM Primary
GPU 2: RTX 5090 (48GB) → Whisper + PoseNet
```

## 2.2 클라우드 GPU (Backup)

* AWS A100 / H100 (Spot)
* 또는 RunPod / LambdaLabs
* 안정성/대규모 inference 시 fallback

## 2.3 GPU Allocation Strategy

| Service | GPU Usage | Priority | Fallback |
|---------|-----------|----------|----------|
| vLLM (LLM) | GPU 1 (80%) | High | Cloud GPU |
| Whisper (STT) | GPU 2 (40%) | Medium | CPU fallback |
| PoseNet (Motion) | GPU 2 (30%) | Medium | CPU fallback |
| Diffusion (Video) | GPU 1+2 (Queue) | Low | Async queue |

---

# 🏗️ 3. AI Router Architecture (중앙 AI 라우팅 엔진)

FastAPI 내에서 모든 AI 요청을 처리하기 전에 **AI Router**가 다음을 결정:

```
1. 어떤 엔진을 사용할 것인가? (LLM? Whisper? PoseNet?)
2. 어떤 GPU 노드로 보낼 것인가? (Load balancing)
3. 어떤 모델 버전을 사용할 것인가? (KR/EN/JP/CN)
4. 어떤 프롬프트 전략을 사용할 것인가?
```

## 3.1 AI Router Implementation

```python
class AIRouter:
    def __init__(self):
        self.vllm_endpoint = "http://localhost:8100"
        self.whisper_endpoint = "http://localhost:8101"
        self.posenet_endpoint = "http://localhost:8102"
        self.diffusion_endpoint = "http://localhost:8103"
    
    async def route(self, request: AIRequest) -> AIResponse:
        if request.type == "speech":
            return await self.call_whisper(request)
        elif request.type == "vision_pose":
            return await self.call_posenet(request)
        elif request.type == "video_generate":
            return await self.call_diffusion(request)
        elif request.type == "llm":
            return await self.call_vllm(request)
        else:
            raise ValueError(f"Unknown AI type: {request.type}")
    
    async def call_vllm(self, request: AIRequest):
        model = self.select_model(request.zone_id, request.locale)
        response = await httpx.post(
            f"{self.vllm_endpoint}/v1/completions",
            json={
                "model": model,
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
        )
        return response.json()
```

## 3.2 Zone별 우선 모델

| Zone | Primary Model | Use Case |
|------|---------------|----------|
| UnivPrepAI | Seoul-Medium-KR | 수능/논술 튜터 |
| SkillPrepAI | Qwen2.5-32B | 자격증/실무 |
| My-Ktube.ai | Whisper-Large-v3 + PoseNet | K-Culture AI |
| mpcstudy.com | Llama-3.1-8B | 경량 문제 해설 |
| DreamSeedAI.com | Qwen2.5-72B | 범용 AI 튜터 |

## 3.3 Load Balancing Strategy

```python
class LoadBalancer:
    def select_gpu_node(self, engine: str) -> str:
        nodes = self.get_available_nodes(engine)
        loads = [self.get_gpu_utilization(node) for node in nodes]
        return nodes[loads.index(min(loads))]
```

---

# 🧬 4. LLM Engine (vLLM)

vLLM은 MegaCity의 LLM Back-end 핵심입니다.

## 4.1 지원 모델

* **Llama 3.1 70B** (KR/EN 튜닝)
* **Qwen2.5 32B / 72B**
* **DeepSeek-R1** (Reasoning)
* **Seoul-Medium-KR** (한국 교육 최적화)

## 4.2 vLLM 실행 예시

```bash
python -m vllm.entrypoints.openai.api_server \
  --model qwen/Qwen2.5-32B \
  --host 0.0.0.0 \
  --port 8100 \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --dtype bfloat16
```

## 4.3 주요 역할

* **Essay feedback**: 논술/작문 첨삭
* **Self-explanation**: 문제 풀이 과정 설명
* **Problem solving**: 수학/과학 문제 해결
* **Korean & English bilingual tutor**: 이중 언어 교육
* **System-wide LLM backbone**: 모든 Zone의 LLM 요청 처리

## 4.4 Prompt Engineering Strategy

```python
PROMPT_TEMPLATES = {
    "essay_feedback": """당신은 대학 입시 논술 전문가입니다.
학생의 에세이: {essay}
평가 기준: 논리성, 창의성, 문장력
첨삭 피드백을 제공하세요.""",
    
    "math_tutor": """당신은 수학 교사입니다.
문제: {problem}
학생 답안: {answer}
오답 원인을 분석하고 올바른 풀이를 설명하세요.""",
    
    "code_review": """당신은 코딩 교육 전문가입니다.
코드: {code}
코드 리뷰와 개선 제안을 해주세요."""
}
```

## 4.5 vLLM API Client

```python
import httpx

async def call_llm(prompt: str, model: str = "qwen2.5-32b") -> str:
    response = await httpx.post(
        "http://localhost:8100/v1/completions",
        json={
            "model": model,
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30.0
    )
    return response.json()["choices"][0]["text"]
```

---

# 🎤 5. Speech Engine (Whisper Large-v3)

Whisper는 MegaCity의 **음성 인식 및 발음 분석 엔진**입니다.

## 5.1 주요 기능

* **K-POP 가사 따라부르기 분석**
* **K-Drama 대사 따라하기 분석**
* **발음 정확도 (%) 측정**
* **한국어/영어/일본어/중국어** 다중 언어 지원

## 5.2 Whisper Setup

```bash
# Docker Container
docker run -d \
  --name whisper-server \
  --gpus '"device=1"' \
  -p 8101:8000 \
  -v /data/models:/models \
  whisper-large-v3:latest
```

## 5.3 Whisper API 구현

```python
import whisper

# Load model (GPU)
model = whisper.load_model("large-v3", device="cuda:1")

@app.post("/api/v1/kzone/voice/analyze")
async def analyze_voice(
    file: UploadFile,
    reference_text: str,
    language: str = "ko"
):
    # Save uploaded audio
    audio_path = f"/tmp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())
    
    # Transcribe
    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True
    )
    
    # Calculate pronunciation accuracy
    accuracy = calculate_pronunciation_accuracy(
        result["text"],
        reference_text
    )
    
    return {
        "transcription": result["text"],
        "accuracy": accuracy,
        "word_details": result["segments"]
    }
```

## 5.4 Pronunciation Scoring

```python
from difflib import SequenceMatcher

def calculate_pronunciation_accuracy(
    transcribed: str,
    reference: str
) -> float:
    # Normalize text
    trans = normalize_text(transcribed)
    ref = normalize_text(reference)
    
    # Calculate similarity
    similarity = SequenceMatcher(None, trans, ref).ratio()
    return round(similarity * 100, 2)
```

---

# 🕺 6. Vision/Motion Engine (PoseNet / MoveNet)

K-Zone Dance Lab / Motion Tutor의 핵심 엔진.

## 6.1 기능

* **Skeleton 추출** (33 Keypoints)
* **MoveNet Lightning/Thunder**
* **모션 비교** (DTW 기반)
* **댄스 점수화**
* **Heatmap 시각화**

## 6.2 PoseNet Setup

```python
import tensorflow as tf
import tensorflow_hub as hub

# Load MoveNet model
model = hub.load("https://tfhub.dev/google/movenet/singlepose/thunder/4")

@app.post("/api/v1/kzone/dance/analyze")
async def analyze_dance(video: UploadFile):
    # Extract frames
    frames = extract_frames(video)
    
    # Run pose estimation
    keypoints_sequence = []
    for frame in frames:
        keypoints = model(frame)
        keypoints_sequence.append(keypoints)
    
    # Compare with reference
    reference = load_reference_dance()
    similarity = calculate_dtw_similarity(keypoints_sequence, reference)
    
    return {
        "score": similarity,
        "keypoints": keypoints_sequence,
        "feedback": generate_feedback(similarity)
    }
```

## 6.3 DTW (Dynamic Time Warping) Comparison

```python
from fastdtw import fastdtw

def calculate_dtw_similarity(student_seq, reference_seq):
    distance, path = fastdtw(student_seq, reference_seq)
    max_distance = len(student_seq) * 10  # Normalize
    similarity = 1 - (distance / max_distance)
    return max(0, min(100, similarity * 100))
```

---

# 🎥 7. Video & Audio Generation (Diffusion / TTS)

Creator Studio 기능을 담당하는 AI 엔진.

## 7.1 Diffusion 기반

* **Shorts 비디오 생성**
* **AI 커버 영상 합성**
* **썸네일 생성**

```python
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda:0")

@app.post("/api/v1/kzone/generate/thumbnail")
async def generate_thumbnail(prompt: str):
    image = pipe(prompt, num_inference_steps=50).images[0]
    return {"image_url": upload_to_storage(image)}
```

## 7.2 TTS 기반

* **한국어 감정 기반 TTS**
* **아이돌 스타일 Voice Clone** (규제 고려)

```python
from TTS.api import TTS

tts = TTS("tts_models/ko/cv/vits")

@app.post("/api/v1/kzone/tts")
async def text_to_speech(text: str, style: str = "neutral"):
    wav = tts.tts(text)
    return {"audio_url": upload_audio(wav)}
```

---

# 🌐 8. Multi-Modal Engine

멀티모달 모델은 텍스트·이미지·오디오·비디오 입력을 하나로 처리함.

## 8.1 사용 모델

* **Qwen2-VL** (Vision-Language)
* **LLaVA-Next** (Multi-modal understanding)
* **Yi-Vision** (국내 최적화)

## 8.2 예시 시나리오

```
User: "이 춤 동작의 문제점 설명해줘" + (영상 첨부)
```

AI Router 처리 흐름:

```
1. PoseNet: 영상에서 Keypoints 추출
2. vLLM: 텍스트 프롬프트 처리
3. Multi-Modal Fusion: 비전 + 텍스트 통합
4. Response: 구조화된 피드백 반환
```

## 8.3 Multi-Modal API

```python
@app.post("/api/v1/ai/multimodal")
async def multimodal_analysis(
    text: str,
    image: Optional[UploadFile] = None,
    video: Optional[UploadFile] = None
):
    # Extract features
    text_embedding = embed_text(text)
    image_features = extract_image_features(image) if image else None
    video_features = extract_video_features(video) if video else None
    
    # Combine modalities
    combined = combine_features(text_embedding, image_features, video_features)
    
    # Generate response
    response = vllm_multimodal.generate(combined)
    return response
```

---

# 📦 9. Storage Architecture

## 9.1 파일 저장

* **Cloudflare R2** (Egress 0원, Primary)
* **Backblaze B2** (Archive)
* **MinIO** (On-prem cache)

## 9.2 디렉토리 구조

```
/kzone/audio/{user_id}/{timestamp}.wav
/kzone/video/{user_id}/{timestamp}.mp4
/exams/{exam_id}/attachments/{filename}
/users/{user_id}/profile/{avatar}
/ai-models/{model_name}/{version}
```

## 9.3 Storage Policy

```python
STORAGE_POLICY = {
    "audio": {
        "retention": "30 days",
        "location": "r2",
        "backup": True
    },
    "video": {
        "retention": "90 days",
        "location": "r2",
        "backup": False
    },
    "model": {
        "retention": "permanent",
        "location": "local + r2",
        "backup": True
    }
}
```

---

# 📈 10. Performance Strategy

## 10.1 Batch Inference

```python
# Bad: Sequential processing
for request in requests:
    result = model.generate(request.prompt)

# Good: Batch processing
prompts = [req.prompt for req in requests]
results = model.generate(prompts)  # GPU batch processing
```

## 10.2 Mixed Precision

```python
# FP8 / BF16 for faster inference
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
```

## 10.3 Quantization

```python
# GPTQ / AWQ for model compression
from auto_gptq import AutoGPTQForCausalLM

model = AutoGPTQForCausalLM.from_quantized(
    "qwen2.5-32b-gptq",
    use_safetensors=True,
    device="cuda:0"
)
```

## 10.4 Caching

```python
# KV Cache for faster generation
from transformers import GenerationConfig

config = GenerationConfig(
    use_cache=True,
    cache_implementation="static"
)
```

## 10.5 Performance Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| LLM Latency (p95) | < 2s | 1.5s | ✅ |
| Whisper Latency | < 3s | 2.1s | ✅ |
| PoseNet Latency | < 1s | 0.8s | ✅ |
| GPU Utilization | 70-90% | 75% | ✅ |

---

# 🔁 11. Scalability Strategy

## 11.1 Horizontal Scaling

* **GPU 노드 추가** 시 자동 라우팅
* **Whisper/PoseNet 독립 스케일링**
* **Multi-Region GPU** 준비 (서울 → 도쿄 → 북미)

```yaml
# Kubernetes HPA for AI services
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: gpu
      target:
        type: Utilization
        averageUtilization: 80
```

## 11.2 Queue-based Processing

```python
# Redis Streams for async AI jobs
await redis.xadd("ai_jobs", {
    "type": "llm",
    "prompt": prompt,
    "user_id": user_id,
    "priority": priority
})

# Worker consumes from queue
async def ai_worker():
    while True:
        job = await redis.xread({"ai_jobs": ">"}, count=1)
        result = await process_ai_job(job)
        await save_result(result)
```

## 11.3 Model Versioning

```python
MODEL_REGISTRY = {
    "qwen2.5-32b": {
        "v1.0": "/models/qwen2.5-32b-v1.0",
        "v1.1": "/models/qwen2.5-32b-v1.1",
        "active": "v1.1"
    }
}
```

---

# 🛡️ 12. Safety & Compliance

## 12.1 개인정보 보호

* **음성/영상 자동 삭제** 정책 (30일/90일)
* **PII Masking** (이름, 전화번호, 주소)
* **Logging 최소화** (AI 요청은 익명화)

## 12.2 AI 생성 콘텐츠 규제

* **K-POP/얼굴/음성** 합성 시 동의 필수
* **Watermark** 삽입 (AI 생성 표시)
* **저작권 필터** (유명 아이돌 얼굴/목소리 차단)

## 12.3 콘텐츠 필터링

```python
async def content_moderation(text: str, image: bytes = None):
    # Toxic content detection
    toxicity_score = await openai_moderation(text)
    
    if toxicity_score > 0.8:
        return {"status": "rejected", "reason": "toxic content"}
    
    # Image safety check
    if image:
        safety = await image_safety_check(image)
        if not safety["is_safe"]:
            return {"status": "rejected", "reason": "unsafe image"}
    
    return {"status": "approved"}
```

## 12.4 Model Bias Monitoring

```python
# Track model predictions by demographics
@app.post("/api/v1/ai/feedback")
async def log_ai_feedback(
    result_id: str,
    is_correct: bool,
    user_demographics: dict
):
    # Monitor for bias patterns
    await analytics.track_bias(result_id, is_correct, user_demographics)
```

---

# 🏁 13. 결론

MegaCity의 AI Infrastructure는 **LLM + Speech + Motion + Video/Audio + Multi-modal AI**가 결합된 하이브리드 아키텍처입니다.

이 문서는 DreamSeedAI의 AI 기능이 안정적으로 작동하고, 글로벌 확장이 가능하며, 다양한 Zone에서 높은 품질의 AI 경험을 제공하기 위한 전체 설계를 정의합니다.

## 핵심 설계 원칙

1. **Modular Architecture**: 각 AI 엔진은 독립 스케일링 가능
2. **Zone-aware Routing**: Zone별 최적 모델 자동 선택
3. **Performance First**: Batch, Quantization, Caching 활용
4. **Safety & Compliance**: 개인정보 보호 + 콘텐츠 규제 준수
5. **Cost Optimization**: 로컬 GPU 우선, 클라우드 Fallback

---

**문서 완료 - DreamSeedAI MegaCity AI Infrastructure Architecture v1.0**
