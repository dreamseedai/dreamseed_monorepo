# 📘 MegaCity Product Requirement Book (PRB)

## 9개 Zone 전체 기능 사양 · Teacher/Student/Parent/K-Zone/Creator Studio · Core System Requirements

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI Product · Architecture Team

---

# 📌 0. 개요 (Introduction)

MegaCity Product Requirement Book(PRB)은 DreamSeedAI 9개 Zone 전체 기능을 통합한 **제품 요구사항 사양서(Full PRD)**입니다.

이 문서는 DreamSeedAI 제품팀, 엔지니어링팀, AI팀이 공통으로 참조하는 **MegaCity 제품 명세의 단일 출처(Single Source of Truth)**입니다.

포함 내용:

```
1. Product Philosophy
2. Core System Requirements
3. Zone-specific Requirements (9 Zones)
4. Teacher Dashboard Requirements
5. Student App Requirements
6. Parent App Requirements
7. K-Zone (Voice/Motion/Drama) Requirements
8. Creator Studio Requirements
9. Admin Console Requirements
10. API & Backend Requirements
11. UX Requirements & Flowcharts
12. Testing/QA Requirements
13. Release Criteria
```

---

# 🌟 1. Product Philosophy (제품 철학)

DreamSeedAI MegaCity 제품은 다음 원칙을 기반으로 설계됩니다.

### 1) AI-Native Product

AI가 보조가 아니라 제품의 중심.

### 2) Personalized Education

학생별 맞춤형 능력·경로·속도 기반 학습.

### 3) Multi-Zone Architecture

각 Zone이 독립적으로 운영되되, 공통 시스템(Core AI / Auth / Payment / Dashboard)을 공유.

### 4) Documented & Observable

모든 기능은 문서화 + 모니터링 가능하도록 설계.

### 5) Safety First

AI Safety, Privacy, Minor Safety를 모든 기능에 우선 적용.

---

# 🧩 2. Core System Requirements

MegaCity 전체 Zone이 공통으로 사용하는 Core 기능.

## 2.1 Authentication & Authorization

* JWT Access Token (15min)
* Refresh Token (7day)
* MFA (교사·학부모 필수)
* Parent–Student Link Flow
* Role-Based Access Control

## 2.2 User Types

```
Student
Parent
Teacher
Tutor
Admin
Creator (K-Zone)
Organization Admin
```

## 2.3 CORE Subsystems

```
CAT/IRT Engine
AI Tutor Engine
Skill Graph Engine
Dashboard Engine
Logging/Audit Engine
Notification Engine
Payment/Billing System
Analytics System
AI Inference Router
```

---

# 🏙️ 3. Zone-specific Product Requirements

MegaCity는 9개의 Zone으로 구성됩니다.
각 Zone은 독립 서비스처럼 작동하지만, Core 시스템을 공유합니다.

## 3.1 UnivPrepAI

* 고등학생 대상 입시 학습 플랫폼
* 모의고사·CAT·개념 학습
* 분석 대시보드 제공

### 주요 기능

```
Exam Session
Adaptive Learning
Concept Review
Progress Report
College Planning (2027~)
```

## 3.2 CollegePrepAI

* 전문대·폴리텍 대비
* 직무형 문제은행
* 실기 기반 학습 일부 포함

## 3.3 SkillPrepAI

* 취업/스킬 기반 커리큘럼
* 절차형 Task 기반 평가
* 직무 시뮬레이션(2027~)

## 3.4 MediPrepAI

* 간호/의료 기초
* 안전성 높은 교육 필요
* Lab Simulation (2028~)

## 3.5 MajorPrepAI

* 전공/대학원 학습 District
* Research Writing
* Presentation Feedback (2028~)

## 3.6 My-Ktube.com

* K-POP/K-Drama 기반 학습 Zone
* 콘텐츠 중심
* 한국어 학습 마이크로 코스

## 3.7 My-Ktube.ai

* 멀티모달 AI Zone (Voice/Motion/Drama)
* Voice Tutor / Dance Lab / Drama Coach

## 3.8 mpcstudy.com

* 무료 공공 교육 Zone
* DreamSeedAI AI Tutor Lite 연결

## 3.9 DreamSeedAI Portal

* MegaCity 전체 관문
* 계정/프로필/도시 지도/로그인 허브

---

# 🧑‍🏫 4. Teacher Dashboard Requirements

## 4.1 기능 목록

```
Class Management
Student Profiles
Exam Creation
Assignment Scheduling
Analytics Dashboard
Parent Communication
```

## 4.2 Teacher Flow

```
Login → Class 선택 → 학생 선택 → 학습 분석 → AI 추천 → 과제 배포
```

---

# 👩‍🎓 5. Student App Requirements

### 핵심 기능

```
Daily Learning Loop
Adaptive Exam
AI Tutor Feedback
Skill Graph Progress
Achievement/Badges
```

### Student Flow

```
Login → My Dashboard → Today's Study → AI Tutor → Next Steps
```

---

# 👨‍👩‍👧 6. Parent App Requirements

### 기능

```
자녀 학습 현황
자녀 시험 분석 리포트
학습 경고 알림
학습 목표 설정
Parent–Student Link Flow
```

---

# 🎤 7. K-Zone (Voice/Motion/Drama) Requirements

## 7.1 Voice Tutor

* Whisper 기반 발음 분석
* Prosody scoring
* Emotion detection
* Native-like pronunciation output

## 7.2 Dance/Motion Tutor

* PoseNet/Movenet keypoints
* Similarity score
* DTW alignment
* 구간별 피드백

## 7.3 Drama Coach

* 억양/표정 기반 감정 인식
* 대사 따라하기
* AI 연기 코칭

---

# 🎬 8. Creator Studio Requirements

## 8.1 기능 목록

```
AI Voice Generation
AI Motion Synthesis
AI Video Remix
Auto-editing (TikTok/Shorts)
Template Gallery
```

## 8.2 Processing Pipeline

```
Upload → Preprocess → AI Model → Render → Publish
```

---

# 🔧 9. Admin Console Requirements

```
User Management
Organization Management
Zone Health Monitoring
Audit Log Viewer
Incident Management
AI Usage Monitoring
Billing Management
```

---

# 🔌 10. API Requirements

## 10.1 인증 관련 API

```
POST /auth/login
POST /auth/register
POST /auth/refresh
POST /auth/parent-link
```

## 10.2 Core API

```
GET /dashboard/teacher
GET /dashboard/parent
POST /exam/start
POST /attempt/submit
GET /skill-graph
```

## 10.3 K-Zone API

```
POST /voice/analyze
POST /motion/analyze
POST /drama/coach
POST /creator/generate
```

---

# 🖥️ 11. UX Requirements

## 11.1 공통 UI 구성 요소

```
Top Navigation
Zone Selector
AI Tutor Pane
Progress Card
Skill Graph View
```

## 11.2 Flowcharts

* Student Learning Flow
* Teacher Assignment Flow
* Parent Monitoring Flow
* K-Zone Voice/Motion Flow

---

# 🧪 12. Testing & QA Requirements

```
Unit Tests (>80% coverage)
E2E Tests (Playwright)
Load Tests (k6)
AI Quality Tests (Dataset 기반)
Device Tests (Mobile)
```

---

# 🚀 13. Release Criteria

```
모든 PRD 항목 충족
문서화 100%
테스트 통과
보안 검증 완료
AI Safety 평가 포함
```

---

# 🏁 결론

MegaCity Product Requirement Book(PRB)은 9개 Zone 전체 기능을 설계하고 개발하기 위한
**제품 개발의 단일 기준**입니다.

이 문서 기반으로 MegaCity 전체 기능이 일관성과 확장성을 유지하며
전 세계 학생·교사·학부모·크리에이터에게 통합적 학습 경험을 제공합니다.
