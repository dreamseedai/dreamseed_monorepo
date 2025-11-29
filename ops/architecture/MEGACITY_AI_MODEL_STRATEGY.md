# 🧠 DreamSeedAI MegaCity – AI Model Strategy Guide

## Zone별 AI 모델 선정 · LLM 라우팅 정책 · Multilingual 전략 · Multi-Modal 모델 구성

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI AI Systems · Architecture Division

---

# 📌 0. 개요 (Overview)

MegaCity는 9개 Zone에서 **교육 · 발음 · 문항 · Motion · 한국어 · 드라마 연기 · Creator Studio** 등 완전히 다른 형태의 AI 기능을 제공합니다.

이를 위해 단일 LLM이 아닌, **Zone 맞춤형 모델 전략 + LLM Routing Layer + Multi-modal Pipeline**이 필요합니다.

본 문서는 MegaCity 전체 AI 모델 전략의 기준이 되는 공식 문서입니다.

**포함 내용:**

```
1. Zone별 AI 모델 선택 기준
2. LLM Routing Layer (7B/14B/34B/70B)
3. 한국어/영어/중국어 Multilingual 전략
4. K-Zone Multi-Modal 모델 구성 (Voice + Motion + Vision)
5. AI Safety Layer · Bias Control
6. 모델 운영 전략(GPU/Scale/Versioning)
```

---

# 🧭 1. MegaCity AI Architecture Overview

전체 AI 구성은 다음 4개의 모델 레이어로 구성됩니다:

```
[Layer 1] Lightweight Models (7B)
[Layer 2] Mid-range Models (14B–32B)
[Layer 3] High-capacity Models (70B)
[Layer 4] Multi-modal Models (Vision + Audio + Motion)
```

각 Layer는 다른 Zone과 Task에 매핑됩니다.

---

# 🧩 2. Zone별 AI 모델 전략 (Core)

각 Zone은 교육 목적·문화 목적·기술 목적이 달라 **다른 모델 전략**을 사용합니다.

## 🎓 2.1 UnivPrepAI (대학 입시 교육)

추천 모델:

```
KR Education → Llama 3.1 14B KR tuned
Math/Physics → DeepSeek-Math 7B
Essay Feedback → Llama 3.1 34B
```

LLM Routing Rule:

```
short-answer → 7B
long-form feedback → 34B
math reasoning → DeepSeek 7B
```

---

## 🧪 2.2 SkillPrepAI (기술/자격증)

추천 모델:

```
Procedural Tutoring → 14B
Safety/Protocol Explanation → 34B
```

특징:

* 기술 매뉴얼 기반 Q/A
* 현장 직무용 안전문구/지침 강조 (AI Safety Layer 강화)

---

## 🏫 2.3 CollegePrepAI

추천 모델:

```
Academic reasoning → 14B
Essay/Portfolio → 34B
Study Plan → 14B
```

특징:

* 대학 포트폴리오/자기소개 평가 지원

---

## 🩺 2.4 MediPrepAI (간호/보건)

강화 규제 구역. AI Safety Layer 최우선.

```
Medical knowledge summary → 7B
Nursing concept explanation → 14B
```

금지:

* 진단/치료 조언 금지
* "당신은 의사가 아닙니다" 문구 자동 삽입

---

## 🎓 2.5 MajorPrepAI (전공/대학원 준비)

```
Research reasoning → 34B
Literature review → 70B
Technical Q/A → 14B
```

고급 학술 지원을 위한 Zone.

---

## 🎮 2.6 My-Ktube.com (K-Culture + Hangul Learning)

언어 + 발음 중심 Zone.

```
Korean conversation → 7B
Hangul error correction → KR 14B
Dialogue learning → 14B
```

---

## 🎤 2.7 My-Ktube.ai (Voice + Motion + Drama + Creator)

멀티모달 핵심 Zone.  
사용 모델:

```
Whisper Large-v3 — STT
PoseNet / MoveNet — Motion
Face/Emotion Encoder — Vision
LLM 34B/70B — Multi-modal reasoning
Diffusion — Creator Studio
```

---

## 🎁 2.8 mpcstudy.com (공공 서비스)

최저 비용 영역:

```
Math/English → 7B
Korean language → 7B KR tuned
```

목표: Low-cost, high-throughput

---

# 🔀 3. LLM Routing Strategy (핵심)

LLM Router는 다음 요소로 모델을 선택합니다:

```
1) Zone
2) Task
3) User language
4) Device capability (mobile/web)
5) Latency budget
```

## 3.1 모델 라우팅 매핑

```
7B  → 빠른 답변, 예/아니오, fact lookup
14B → 교육 목적, tutoring
34B → 긴 분석, essay, feedback
70B → 고난도 reasoning, multi-modal
```

## 3.2 언어 기반 라우팅

```
Korean → Llama 3.1 KR
English → Llama 3.1 EN
Chinese → Qwen2.5 14B
Japanese → Japanese-LLM 13B (optional)
```

## 3.3 Latency-based Routing

```
time budget < 1s → 7B
simple Q/A → 14B
complex → 34B
multi-modal → 70B
```

---

# 🌍 4. Multilingual Strategy

MegaCity는 KR/EN/CN을 기본으로 지원.

## 4.1 기본 정책

* 한국 학생 → KR 모델 우선
* 국제 학생 → EN/JA/CN 자동 감지
* My-Ktube → KR 우선, EN fallback

## 4.2 언어 감지(Language Detection)

Whisper/fastText 기반 자동 감지.

---

# 🤖 5. Multi-Modal Model Strategy (K-Zone 중심)

K-Zone은 다음 4개 모델을 통합해 multi-modal tutor를 구성합니다.

## 5.1 Voice (Speech)

* Whisper Large-v3
* Prosody analyzer
* Emotion classifier

## 5.2 Motion (Pose)

* MoveNet/BlazePose
* DTW-based motion compare

## 5.3 Vision (Face/Scene)

* Face mesh
* Expression encoder
* Scene detector

## 5.4 LLM (Reasoning)

* 34B/70B multi-modal pipeline

---

# 🛡️ 6. AI Safety Strategy

## 6.1 Prompt Firewall

금지 토큰/패턴 필터링.

## 6.2 Output Moderation

* 욕설/혐오/음란 표현 자동 필터
* Drama Coach: 위험 스크립트 차단

## 6.3 Bias Control

* 국적/성별/종교 편향 탐지
* Education Zone: 중립적 설명 우선

---

# 🖥️ 7. Model Hosting & Scaling Strategy

## 7.1 vLLM 기반 LLM Hosting

```
vLLM + Tensor parallel + KV cache reuse
```

## 7.2 Whisper Hosting

GPU당 동시 요청 2–5개.

## 7.3 Pose Hosting

CPU+GPU 혼합 처리.

## 7.4 Model Versioning

```
model_v1 → 안정화
model_v2 → 품질 개선
model_v3 → multi-modal 통합
```

---

# 🏁 8. 결론

MegaCity AI Model Strategy는 Zone 기반·언어 기반·Task 기반으로 **최적의 모델을 자동 선택**하는  
LLM Routing Layer를 중심으로 구성됩니다.

이 전략은 MegaCity가 2027–2028년에 **Global Multi-modal AI City**로 성장하기 위한 핵심 기반입니다.
