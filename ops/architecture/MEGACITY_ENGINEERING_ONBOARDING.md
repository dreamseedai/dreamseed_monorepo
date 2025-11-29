# 🧩 DreamSeedAI – Engineering Onboarding Pack

## 신입 엔지니어 1주 완성 온보딩 패키지 (Backend · Frontend · AI · DevOps · Governance 핵심 요약)

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI Engineering Leadership

---

# 📌 0. 소개

이 문서는 DreamSeedAI 신입 엔지니어가 **1주일 내 전체 시스템을 빠르게 이해**할 수 있도록 만든 핵심 요약 온보딩 패키지입니다.

DreamSeedAI MegaCity는 1000개 이상의 컴포넌트로 구성된 거대한 시스템이지만,  
이 문서 하나로 전체 시스템의 **구조·작동 방식·코딩 규칙·문화·운영 방식**을 단숨에 이해할 수 있습니다.

본 문서는 다음 10개 챕터로 구성됩니다:

```
1. DreamSeedAI Overview
2. MegaCity Architecture (한눈에 보기)
3. AI Model Strategy (핵심 요약)
4. Backend/API 구조
5. Frontend/Portal 구조
6. DevOps/Gateway/DNS 구조
7. Security & Governance 요약
8. Coding Rules (Backend·Frontend·AI)
9. 신규 엔지니어 1주일 플랜
10. Repository Map (레포 탐색 가이드)
```

---

# 🏙️ 1. DreamSeedAI Overview

DreamSeedAI는 교육을 **도시(MegaCity)** 로 바라보고 다음 9개 Zone으로 구성됩니다:

```
UnivPrepAI — 대학 입시
CollegePrepAI — 전문대
SkillPrepAI — 기술/자격증
MediPrepAI — 보건/의료 기초
MajorPrepAI — 전공/연구 준비
My-Ktube.com — K-Culture 학습
My-Ktube.ai — 멀티모달 AI
mpcstudy.com — 공공 교육
DreamSeedAI.com — 통합 포털
```

MegaCity는 단순 서비스 묶음이 아니라 **하나의 도시**로 설계된 AI 플랫폼입니다.

---

# 🧭 2. MegaCity Architecture (핵심 요약)

MegaCity 전체 구조는 다음 6계층으로 구성됩니다:

```
1. Cloudflare Edge (DNS·CDN·WAF)
2. Gateway (Traefik/Nginx)
3. Frontend Cluster (Next.js)
4. Backend Cluster (FastAPI)
5. Data Layer (PostgreSQL + Redis)
6. AI Layer (vLLM·Whisper·PoseNet)
```

### 아키텍처 맵

```
Cloudflare Edge
   ↓
Gateway (Traefik/Nginx)
   ↓
app.<zone>.com  →  Next.js
api.<zone>.com  →  FastAPI
static.<zone>.com → R2/MinIO
   ↓
PostgreSQL / Redis
   ↓
GPU Cluster (LLM·Whisper·PoseNet)
```

---

# 🧠 3. AI Model Strategy 요약

DreamSeedAI는 단일 LLM이 아니라, **Zone·Task·언어 기반 라우팅 전략**을 사용합니다.

### 핵심 LLM

```
7B → 빠른 답변
14B → 교육·튜터링
34B → Essay/피드백
70B → 멀티모달/Deep reasoning
```

### Zone별 라우팅

```
UnivPrep → KR Education (14B)
SkillPrep → Procedure Tutor (14B)
K-Zone (My-Ktube.ai) → Whisper + PoseNet + 34B/70B
mpcstudy → 7B (저비용)
```

### Multi-modal

* Whisper: 발음, 억양, 감정
* PoseNet: Dance/Motion
* Vision Encoder: 표정/연기
* LLM: 해석/피드백/설명

---

# 🛠️ 4. Backend/API 구조 (FastAPI)

### 주요 디렉토리 구조

```
backend/app/
 ├─ api/ (라우터)
 ├─ models/ (SQLAlchemy ORM)
 ├─ schemas/ (Pydantic)
 ├─ services/ (비즈니스 로직)
 ├─ core/ (설정/보안)
 ├─ db.py
 └─ main.py
```

### 핵심 엔티티

```
User / Student / Teacher
Class / Enrollment
Exam / Item / Attempt
Analytics
K-Zone AI Metadata
```

### 주요 기술

* FastAPI + SQLAlchemy 2.0
* Alembic migration
* JWT Auth + RBAC/PBAC
* Redis Rate Limit
* Pydantic v2 models

---

# 🎨 5. Frontend/Portal 구조 (Next.js)

### 디렉토리 구조

```
frontend/
 ├─ app/ (App Router)
 ├─ components/
 ├─ features/
 ├─ hooks/
 └─ utils/
```

### Zone Portal 구조

```
DreamSeedAI.com → 통합 포털
app.univprepai.com
app.skillprepai.com
app.my-ktube.com
```

### 주요 기술

* Next.js 14 (App Router)
* TanStack Query
* TailwindCSS
* Recharts (Dashboard)
* next-intl (다국어)

---

# 🔧 6. DevOps/Gateway/DNS 구조

### Cloudflare 설정 (전 Zone 공통)

```
SSL: Full (Strict)
Always HTTPS: ON
HSTS: ON
WAF: Enabled
Rate Limit: api.<zone>.com
```

### Reverse Proxy

* Traefik (Docker-native)
* Nginx (고성능/정적 구조)

### 배포

* GitHub Actions → Docker → Traefik
* Blue-Green/Canary 지원

### 모니터링

* Prometheus + Grafana
* Loki Logs
* AlertManager

---

# 🛡️ 7. Security & Governance 요약

### 보안 원칙

```
Security by Default
Least Privilege
PII Encryption
Audit Logging
```

### PBAC 정책

* zone_id + org_id + role 기반 접근 제어
* Parent–Student 승인 Flow

### 규제 준수

* GDPR / PIPA / COPPA / FERPA
* 영상/음성 7~30일 후 삭제

---

# ✍️ 8. Coding Rules

### Backend

```
Black/Flake8
함수는 20~40줄 유지
서비스 레이어 분리
Pydantic 스키마 일관화
API는 OpenAPI 자동 문서화
```

### Frontend

```
컴포넌트는 작은 단위
Server Component 우선
TanStack Query로 데이터 관리
```

### AI

```
모델 버전 태깅 필수
Whisper/PoseNet Job Queue 사용
GPU 메모리 90% 이상 금지
```

---

# 📅 9. 신입 엔지니어 1주 온보딩 플랜

## Day 1 — 전체 구조 이해

* MegaCity Architecture 읽기
* AI Model Strategy 읽기
* Domain/Network Architecture 훑기

## Day 2 — Backend 집중

* API 구조 익히기
* User/ExamSession/Attempt 엔드포인트 실행
* DB 스키마 이해

## Day 3 — Frontend 집중

* Next.js App Router 구조 익히기
* Teacher/Parent Dashboard 실행

## Day 4 — AI 집중

* Whisper 테스트
* vLLM 서버 쿼리
* PoseNet 샘플 분석

## Day 5 — DevOps 집중

* Cloudflare 설정 이해
* Traefik 경로 확인
* GitHub Actions 빌드 확인

## Day 6 — Mini Project

* "Exam + Attempt" end-to-end 구현

## Day 7 — 리뷰 & 정리

* 질문 목록 정리
* Architecture Team과 리뷰

---

# 🗺️ 10. Repository Map (레포 탐색 가이드)

```
dreamseed_monorepo/
 ├─ backend/
 ├─ frontend/
 ├─ ai/
 ├─ ops/
 │    ├─ dns/
 │    ├─ reverse_proxy/
 │    ├─ monitoring/
 │    └─ scripts/
 ├─ docs/
 └─ tools/
```

---

# 🏁 결론

이 Engineering Onboarding Pack은 DreamSeedAI MegaCity 전체를  
**1주일 만에 이해하고 기여할 수 있는 엔지니어링 지침서**입니다.

신규 팀원은 이 문서를 기반으로 빠르게 생산성을 확보하며,  
DreamSeedAI의 글로벌 MegaCity 개발에 즉시 참여할 수 있습니다.
