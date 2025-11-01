# V1 Implementation Status Report

**Generated**: 2025-10-31  
**Purpose**: Track completion of V1 In-Scope (Tutor-only) features  
**North Star**: TTFP ≤60분, 14일 재시험율 ≥40%, 트라이얼→유료 전환 ≥20%

---

## 📊 Overview

| Item | Status | Completion | Priority | Blockers |
|------|--------|------------|----------|----------|
| 1. Wizard | 🟡 Partial | 40% | P0 | Missing onboarding flow, no exam setup UI |
| 2. Exam | 🟢 Core Ready | 75% | P0 | PDF generation stub (501), no real-time grading UI |
| 3. Assign | 🔴 Not Started | 10% | P1 | No student invite flow, missing classroom UI |
| 4. Payment | 🟡 Partial | 50% | P1 | Stripe integration exists, needs tutor-specific flow |
| 5. Logging | 🟢 Ready | 80% | P2 | Sentry configured, missing Amplitude integration |

**Overall V1 Readiness**: ~50% (weighted average)

---

## 1. Wizard (튜터 온보딩, 시험 설정)

### 🎯 Goal
튜터가 처음 방문하여 첫 시험 PDF를 생성하기까지의 온보딩 프로세스

### ✅ Implemented
- ❌ **None** - No dedicated wizard flow detected

### 🟡 Partial
- **Profile Selection** (`portal_front/src/components/ProfileSelect.tsx`)
  - Country/Grade/Goal selection UI exists
  - Calls `/api/recommend` for personalized recommendations
  - **Gap**: Not tutor-focused, designed for student/parent perspective

### ❌ Missing (Critical Path)
1. **Tutor Onboarding Wizard**
   - Step 1: Welcome + Role confirmation (teacher)
   - Step 2: School/Organization setup
   - Step 3: Exam type selection (diagnostic, practice, assessment)
   - Step 4: PDF generation preview
   - **Impact**: Direct blocker for TTFP ≤60분

2. **Exam Setup UI**
   - Topic selection interface
   - Difficulty level controls
   - Question count configuration
   - Time limit settings
   - **Impact**: Without this, tutors cannot customize exams

### 📝 Implementation Plan
```
Priority: P0 (Critical)
Estimated Lines: ~300 (≤150 per file, split into 3 components)
Files to Create:
- portal_front/src/pages/TutorWizard.tsx (≤150 lines)
- portal_front/src/components/ExamSetupForm.tsx (≤150 lines)
- apps/seedtest_api/routers/wizard.py (≤150 lines)

Completion ETA: 3-5 days
```

---

## 2. Exam (시험 생성, PDF 다운로드, 채점)

### 🎯 Goal
적응형 시험 생성, PDF 다운로드, 자동 채점 및 결과 분석

### ✅ Implemented (Core Engine)
- **Exam Creation API** (`apps/seedtest_api/routers/exams.py`)
  - `POST /api/seedtest/exams` - Session creation ✅
  - `GET /api/seedtest/exams/{session_id}/next` - Next question ✅
  - `POST /api/seedtest/exams/{session_id}/answer` - Submit answer ✅
  - `POST /api/seedtest/exams/{session_id}/finish` - Finalize session ✅

- **Adaptive Engine** (`apps/seedtest_api/services/adaptive_engine.py`)
  - IRT-based question selection ✅
  - Difficulty adjustment ✅
  - Session state management ✅

- **Result Computation** (`apps/seedtest_api/routers/results.py`)
  - `POST /api/seedtest/exams/{session_id}/result` - Compute result (idempotent) ✅
  - `GET /api/seedtest/exams/{session_id}/result` - Fetch cached result ✅
  - `GET /api/seedtest/results` - List results with filters ✅

- **Database Schema**
  - `exam_sessions` table with ownership (user_id, org_id) ✅
  - `exam_results` table with JSONB result_json ✅
  - Role-based access control (student/teacher/admin) ✅

### 🟡 Partial (UI & PDF)
- **PDF Generation** (`apps/seedtest_api/routers/results.py:480`)
  - Endpoint exists: `GET /api/seedtest/exams/{session_id}/result/pdf`
  - **Status**: 501 Not Implemented (stub only)
  - **Impact**: Critical blocker for TTFP

- **Frontend Exam UI** (`portal_front/src/pages/`)
  - **Missing**: No dedicated exam-taking interface for students
  - **Missing**: No real-time grading feedback UI
  - **Gap**: Exam guides exist (`USExamsSAT.tsx`, `USExamsAP.tsx`) but no interactive exam flow

### ❌ Missing (High Priority)
1. **PDF Renderer Service**
   - Lambda function stub exists: `infra/pdf_lambda/lambda_function.py`
   - **Required**:
     - Integrate with exam result JSON
     - Generate branded PDF with tutor logo
     - Include score breakdown, question-by-question analysis
     - Support A4/Letter formats
   - **Estimated Lines**: ~200 (split into 2 files ≤150 each)

2. **Exam-Taking UI** (`portal_front/`)
   - Question display component
   - Answer submission interface
   - Progress tracker
   - Timer display
   - **Estimated Lines**: ~250 (split into 2 components)

### 📝 Implementation Plan (PDF Critical Path)
```
Priority: P0 (Blocking TTFP)
Phase 1: PDF Lambda (Week 1)
- infra/pdf_lambda/renderer.py (≤150 lines)
- infra/pdf_lambda/templates/exam_result.html (≤150 lines)
- Test with sample exam result JSON

Phase 2: Frontend Integration (Week 2)
- portal_front/src/pages/ExamTake.tsx (≤150 lines)
- portal_front/src/components/PDFDownloadButton.tsx (≤50 lines)

Completion ETA: 2 weeks
```

---

## 3. Assign (학생 초대, 시험 배정, 결과 확인)

### 🎯 Goal
튜터가 학생을 초대하고, 시험을 배정하고, 결과를 확인하는 워크플로우

### ✅ Implemented (Backend Foundation)
- **Classroom API** (`apps/seedtest_api/app/api/routers/classrooms.py`)
  - `POST /api/seedtest/classrooms` - Create classroom ✅
  - `GET /api/seedtest/classrooms?org_id=ORG` - List classrooms ✅
  - Role enforcement (teacher/admin only) ✅

- **Session Ownership** (`apps/seedtest_api/models/session.py`)
  - `user_id`, `org_id` columns ✅
  - Role-based access via `require_session_access` dependency ✅

### 🔴 Missing (Critical Path)
1. **Student Invitation System**
   - Email invite endpoint
   - Magic link generation
   - Student signup flow
   - Classroom roster management
   - **Impact**: Cannot assign exams without students
   - **Estimated Lines**: ~300 (split into 3 files)

2. **Exam Assignment UI**
   - Tutor dashboard for classroom management
   - Exam assignment interface (select students + exam)
   - Due date scheduling
   - Notification system
   - **Estimated Lines**: ~400 (split into 3 components)

3. **Results Dashboard**
   - Class-wide results view
   - Individual student performance
   - Export to CSV/Excel
   - **Estimated Lines**: ~250 (split into 2 components)

### 📝 Implementation Plan
```
Priority: P1 (After Wizard + PDF)
Phase 1: Student Invite (Week 3)
- apps/seedtest_api/routers/invitations.py (≤150 lines)
- apps/seedtest_api/services/email_service.py (≤150 lines)
- portal_front/src/pages/StudentInvite.tsx (≤150 lines)

Phase 2: Assignment UI (Week 4)
- portal_front/src/pages/TutorDashboard.tsx (≤150 lines)
- portal_front/src/components/ExamAssignModal.tsx (≤150 lines)

Phase 3: Results View (Week 5)
- portal_front/src/pages/ClassResults.tsx (≤150 lines)
- portal_front/src/components/StudentResultCard.tsx (≤100 lines)

Completion ETA: 3 weeks (after Phase 1 & 2 complete)
```

---

## 4. Payment (튜터 개인 결제)

### 🎯 Goal
튜터가 개인 신용카드로 월 구독료 결제

### ✅ Implemented (Stripe Integration)
- **Billing API** (`portal_front/src/lib/billing.ts`, `portal_front/src/lib/pay.ts`)
  - `POST /api/billing/stripe/create-checkout-session` ✅
  - `POST /api/billing/stripe/portal` - Manage subscription ✅
  - `GET /api/billing/stripe/status` - Check subscription status ✅
  - `GET /api/billing/stripe/events` - List Stripe events ✅
  - `GET /api/billing/stripe/expiring` - Expiring subscriptions ✅

- **Frontend Components**
  - `SubscribedBadge.tsx` - Show subscription status ✅
  - `ExpiringCard.tsx` - Display expiring subscriptions ✅
  - `Success.tsx`, `Cancel.tsx` - Checkout result pages ✅

### 🟡 Partial (Tutor-Specific Flow)
- **Gap**: Existing payment flow is generic (not tutor-focused)
- **Missing**:
  - Tutor pricing tier (vs. student pricing)
  - Organization-level billing (for schools)
  - Trial period management (14-day trial → paid)

### ❌ Missing
1. **Tutor Pricing Page**
   - Clear pricing tiers (Solo Tutor vs. Tutoring Business)
   - Feature comparison table
   - Trial CTA ("Start 14-day Free Trial")
   - **Estimated Lines**: ~150

2. **Trial→Paid Conversion Tracking**
   - Amplitude event: `trial_started`, `trial_converted`, `trial_expired`
   - Email reminders (3 days before trial ends)
   - Conversion dashboard for metrics
   - **Estimated Lines**: ~200 (split into 2 files)

### 📝 Implementation Plan
```
Priority: P1 (After Assign complete)
Phase 1: Tutor Pricing UI (Week 6)
- portal_front/src/pages/TutorPricing.tsx (≤150 lines)
- Update Stripe product/price IDs for tutor tier

Phase 2: Trial Tracking (Week 6)
- apps/seedtest_api/services/trial_service.py (≤150 lines)
- Amplitude integration for conversion events

Completion ETA: 1 week
```

---

## 5. Logging (기본 추적 - Amplitude/CloudWatch)

### 🎯 Goal
튜터 행동 추적 및 에러 모니터링

### ✅ Implemented (Sentry)
- **Error Tracking** (`apps/seedtest_api/app/main.py:63-83`)
  - Sentry SDK initialized if `SENTRY_DSN` env var set ✅
  - FastAPI integration with `sentry_sdk.integrations.fastapi` ✅
  - Environment tags (`SENTRY_ENV`, `SENTRY_RELEASE`) ✅
  - Traces sampling (`SENTRY_TRACES_SAMPLE_RATE`) ✅

- **Basic Logging** (`apps/seedtest_api/app/main.py`)
  - Python `logging` module configured ✅
  - DB connectivity warnings ✅
  - Service startup logs ✅

### 🟡 Partial (CloudWatch)
- **AWS Infrastructure** (`infra/cloudwatch/`)
  - Alarms configuration exists: `alarms-apigw-alb-rds.yaml`
  - **Status**: Out-of-Scope for V1 (per GUARDRAILS.md)
  - **Reason**: Infrastructure고도화 is V2

### ❌ Missing (Amplitude)
1. **Amplitude Integration**
   - Event tracking library (amplitude-python)
   - Key events for V1 metrics:
     - `wizard_started`, `wizard_completed` → TTFP tracking
     - `pdf_downloaded` → First PDF milestone
     - `exam_assigned`, `exam_completed`
     - `trial_started`, `trial_converted` → Conversion rate
   - **Estimated Lines**: ~150

2. **Tutor Metrics Dashboard**
   - View own TTFP (time since signup → first PDF)
   - Trial countdown (days remaining)
   - Student engagement stats
   - **Estimated Lines**: ~150

### 📝 Implementation Plan
```
Priority: P2 (Can parallelize with other work)
Phase 1: Amplitude SDK (Week 7)
- apps/seedtest_api/services/amplitude.py (≤150 lines)
- Instrument key endpoints (wizard, exam, PDF, payment)
- Add AMPLITUDE_API_KEY to .env

Phase 2: Metrics Dashboard (Week 7)
- portal_front/src/pages/TutorMetrics.tsx (≤150 lines)
- Real-time TTFP display
- Trial conversion funnel

Completion ETA: 1 week (can start early)
```

---

## 🚦 Critical Path to V1 Launch

### Phase 1: MVP (Weeks 1-2) - "First PDF in 60 minutes"
1. **Wizard** (P0)
   - Tutor onboarding flow (3-4 steps)
   - Exam setup form
   - ETA: 3-5 days

2. **PDF Generation** (P0)
   - Lambda renderer integration
   - Branded PDF template
   - ETA: 1 week

**Milestone**: Tutor can generate first PDF ≤60분 ✅

### Phase 2: Assign & Track (Weeks 3-5)
3. **Assign** (P1)
   - Student invitation system
   - Exam assignment UI
   - Results dashboard
   - ETA: 3 weeks

**Milestone**: Tutor can assign exams to students ✅

### Phase 3: Monetization (Week 6)
4. **Payment** (P1)
   - Tutor pricing page
   - Trial→Paid conversion tracking
   - ETA: 1 week

**Milestone**: Trial→유료 전환 측정 가능 ✅

### Phase 4: Observability (Week 7)
5. **Logging** (P2)
   - Amplitude integration
   - Tutor metrics dashboard
   - ETA: 1 week (can parallelize)

**Milestone**: North Star metrics 대시보드 완성 ✅

---

## 📈 V1 Success Metrics (Post-Launch)

| Metric | Target | Measurement | Status |
|--------|--------|-------------|--------|
| **TTFP** | ≤60분 | Amplitude: `wizard_started` → `pdf_downloaded` | 🔴 Not Tracking |
| **14일 재시험율** | ≥40% | SQL: COUNT(DISTINCT user_id) where exam_count ≥2 in 14 days | 🟡 Schema Ready |
| **트라이얼→유료** | ≥20% | Amplitude: `trial_started` → `trial_converted` funnel | 🔴 Not Tracking |

**Action Required**:
1. Implement Amplitude tracking (Week 7)
2. Create Amplitude dashboard with funnels
3. Schedule weekly metric reviews

---

## 🛡️ V1 Guardrails Compliance

### ✅ In-Scope Alignment
All 5 items tracked in this document are **V1 In-Scope**:
- Wizard ✅
- Exam ✅
- Assign ✅
- Payment ✅
- Logging ✅

### ❌ Out-of-Scope Items (Blocked by scope-guard.yml)
- ~~CloudWatch 고도화~~ → V2 (DEBT.md)
- ~~SSO/SAML~~ → V2
- ~~학원 관리 (multi-branch)~~ → V2
- ~~전교/학년 대시보드~~ → V2

### 📏 Dev Contract Compliance
- All implementation plans: **≤150 lines per file** ✅
- Single-purpose PRs enforced by PR template ✅
- No premature abstraction (3회 반복 전까지) ✅

---

## 🔄 Next Steps

1. **Immediate (This Week)**:
   - [ ] Review this status report with team
   - [ ] Prioritize Wizard + PDF (P0) for sprint planning
   - [ ] Assign owners to each phase

2. **Short-term (Next 2 Weeks)**:
   - [ ] Complete Phase 1: MVP (Wizard + PDF)
   - [ ] Test TTFP with 3 real tutors (beta)
   - [ ] Collect feedback on onboarding flow

3. **Mid-term (Weeks 3-7)**:
   - [ ] Complete Phases 2-4 (Assign, Payment, Logging)
   - [ ] Launch V1 to 20 tutors (limited beta)
   - [ ] Measure North Star metrics

4. **Post-Launch**:
   - [ ] Monitor TTFP, 재시험율, 전환율 weekly
   - [ ] Iterate based on tutor feedback
   - [ ] Plan V2 feature prioritization (refer to DEBT.md)

---

**Document Owner**: Engineering Team  
**Last Updated**: 2025-10-31  
**Next Review**: 2025-11-07 (weekly cadence)
