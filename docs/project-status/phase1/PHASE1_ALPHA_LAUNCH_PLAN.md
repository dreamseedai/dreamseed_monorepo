# Phase 1.0 - Alpha Launch Plan (dreamseedai.com)

**Project:** DreamSeed AI Platform  
**Phase:** 1.0 - Alpha Launch  
**Target:** dreamseedai.com 실질적 운영 가능한 알파 버전  
**Date:** November 24, 2025  
**Status:** 📋 **PLANNING**  

---

## Phase 1.0 재정의: 목표 명확화

### 기존 정의 (변경 전)
❌ "Authentication, Security & Advanced Features"
- 너무 기술 중심적
- 실제 사용 시나리오 불명확
- 완료 기준이 모호

### 새로운 정의 (변경 후)
✅ **"dreamseedai.com에서 실질적으로 써볼 수 있는 알파 버전"**
- 학생이 직접 접속해서 시험을 보고 결과를 볼 수 있는 최소 UX 흐름
- 소규모 베타 테스트 가능 (본인 + 가족 + 지인 5-10명)
- 실제 피드백을 받아서 Phase 2 설계에 반영

---

## Phase 1 완료 = 무엇이 가능한가?

### ✅ 가능한 것 (Alpha-Ready)

**1. 실제 URL 접속**
```
https://dreamseedai.com
```
- Cloudflare + SSL 인증서 적용
- 백엔드 API 연결
- 안정적인 DNS 라우팅

**2. 회원가입 & 로그인**
- 이메일 + 비밀번호 회원가입
- JWT 기반 로그인
- 역할 선택 (학생/교사/학부모)

**3. 진단 시험 시작**
- 로그인 후 대시보드
- "Math 진단 테스트 시작" 버튼
- "English 진단 테스트 시작" 버튼
- "Science 진단 테스트 시작" 버튼

**4. 적응형 시험 진행**
- CAT 엔진이 실시간으로 문제 선택
- 학생 답변 제출
- θ (theta) 실시간 업데이트
- Fisher Information 기반 종료 조건 (SE < 0.3)

**5. 시험 결과 확인**
- 추정 실력 θ (theta)
- 표준 점수 (0-100 scale)
- 등급 (A-F or 1-9등급)
- 난이도 분포 (easy/medium/hard)
- 정답률

**6. 소규모 베타 운영**
- 5-10명의 테스터 초대
- 실제 사용 로그 수집
- AI API 비용/성능 모니터링
- 피드백 수집 및 분석

---

### ❌ 아직 불가능한 것 (Phase 2 이후)

**1. 결제/구독 시스템**
- 신용카드 결제
- 구독 플랜 (월간/연간)
- 무료 체험 기간 관리

**2. 교사/학부모 대시보드**
- 학생 진도 모니터링
- 성적 분석 리포트
- 학급 관리 기능

**3. 고급 모니터링/알림**
- 실시간 알림 (시험 완료, 성적 업데이트)
- 이메일 리포트 발송
- Slack/Discord 통합

**4. 대규모 트래픽 대응**
- 1000명 동시 접속
- 오토스케일링 (Kubernetes)
- CDN 최적화

**5. 고급 CAT 기능**
- Multi-stage adaptive testing
- Content balancing with blueprints
- Advanced exposure control

---

## Phase 1.0 Complete UX Flow (알파 버전)

### 시나리오: 학생 "김철수"의 첫 시험

#### Step 1: 접속 및 회원가입 (3분)
```
1. https://dreamseedai.com 접속
2. "회원가입" 버튼 클릭
3. 이메일, 비밀번호, 이름, 학년 입력
4. "학생" 역할 선택
5. 회원가입 완료 → 자동 로그인
```

**Backend API:**
- `POST /api/auth/register`
- `POST /api/auth/login`

**Frontend 화면:**
- 랜딩 페이지 (`/`)
- 회원가입 폼 (`/register`)
- 로그인 폼 (`/login`)

---

#### Step 2: 대시보드 & 시험 선택 (1분)
```
1. 로그인 후 학생 대시보드 표시
2. 진단 시험 목록:
   - Math 진단 테스트 (Level: Adaptive, Items: 10-20)
   - English 진단 테스트 (Level: Adaptive, Items: 10-20)
   - Science 진단 테스트 (Level: Adaptive, Items: 10-20)
3. "Math 진단 테스트 시작" 버튼 클릭
```

**Backend API:**
- `GET /api/adaptive/pools` (available test pools)

**Frontend 화면:**
- 학생 대시보드 (`/student/dashboard`)
- 시험 선택 화면 (`/student/tests`)

---

#### Step 3: 시험 시작 & 첫 문제 (30초)
```
1. 시험 시작 확인 팝업
   "Math 진단 테스트를 시작합니다. 준비되셨나요?"
2. "시작" 버튼 클릭
3. 첫 문제 표시:
   - 문제 번호: 1/10
   - 문제 내용: "다음 방정식을 풀어라: 2x + 5 = 13"
   - 선택지:
     A) x = 3
     B) x = 4  ← 정답
     C) x = 5
     D) x = 6
   - 예상 소요 시간: 1-2분
```

**Backend API:**
- `POST /api/adaptive/exams/start` → returns session_id
- `GET /api/adaptive/exams/{session_id}/next-item` → returns first item

**Frontend 화면:**
- 시험 시작 확인 (`/student/exams/start`)
- 문제 풀이 화면 (`/student/exams/{session_id}/item`)

---

#### Step 4: 답변 제출 & 다음 문제 (반복 10-20회)
```
1. 학생이 "B) x = 4" 선택
2. "제출" 버튼 클릭
3. 즉시 다음 문제 로딩 (1초 이내)
4. CAT 엔진이 θ 업데이트 & 다음 문제 선택
5. 문제 번호: 2/10
   - 난이도 조정 (정답이면 더 어려운 문제, 오답이면 쉬운 문제)
6. 종료 조건 확인:
   - SE(θ) < 0.3 → 종료
   - 최대 문항 수 (20개) → 종료
```

**Backend API (반복):**
- `POST /api/adaptive/exams/{session_id}/submit-answer`
  - Input: `{ "item_id": 123, "choice_id": 456 }`
  - Output: `{ "is_correct": true, "new_theta": 0.5, "se": 0.4 }`
- `GET /api/adaptive/exams/{session_id}/next-item`
  - Output: next item or `{ "finished": true }`

**Frontend 화면:**
- 동일 화면 (`/student/exams/{session_id}/item`)
- 진행률 표시 (Progress bar: 2/10 → 20%)

---

#### Step 5: 시험 완료 & 결과 확인 (2분)
```
1. 마지막 답변 제출
2. "시험이 완료되었습니다!" 메시지
3. 결과 화면 자동 전환:

   ========================================
          Math 진단 테스트 결과
   ========================================
   
   📊 추정 실력 (θ):     0.75
   📈 표준 점수:         67점 / 100점
   🏆 등급:             B (상위 30%)
   
   ----------------------------------------
   문제 난이도 분포:
   ----------------------------------------
   쉬운 문제:    3개 (정답: 3, 정답률: 100%)
   중간 문제:    7개 (정답: 5, 정답률: 71%)
   어려운 문제:  2개 (정답: 0, 정답률: 0%)
   
   ----------------------------------------
   총 문항 수:   12개
   정답 수:      8개
   정답률:       67%
   소요 시간:    8분 23초
   ----------------------------------------
   
   💡 피드백:
   중급 수준의 문제를 잘 풀고 있습니다.
   고급 문제를 더 연습하면 80점 이상 가능합니다.
   
   [다시 시험 보기]  [대시보드로 돌아가기]
```

**Backend API:**
- `GET /api/adaptive/exams/{session_id}/results`
  - Output: theta, score, grade, item statistics

**Frontend 화면:**
- 결과 화면 (`/student/exams/{session_id}/results`)

---

#### Step 6: 대시보드 복귀 & 기록 확인 (1분)
```
1. "대시보드로 돌아가기" 클릭
2. 시험 기록 카드 표시:

   ┌─────────────────────────────────────┐
   │ Math 진단 테스트                    │
   │ 완료 시간: 2025-11-24 14:30        │
   │ 점수: 67점 (B등급)                 │
   │ θ: 0.75                            │
   │ [결과 다시 보기]                    │
   └─────────────────────────────────────┘
   
3. 다른 시험 선택 가능:
   - English 진단 테스트 (아직 안 봄)
   - Science 진단 테스트 (아직 안 봄)
```

**Backend API:**
- `GET /api/adaptive/exams/history` (user's past exams)

**Frontend 화면:**
- 학생 대시보드 (`/student/dashboard`)
- 시험 기록 목록 (`/student/history`)

---

## Phase 1.0 Completion Checklist

### Backend (95% 완성 - Phase 0.5)
- [x] PostgreSQL schema (30 tables)
- [x] CAT/IRT engine (3PL model)
- [x] Seed data (120 items)
- [x] Docker Compose
- [ ] **Authentication (JWT, RBAC)** ← Phase 1 작업
- [ ] **API endpoints for UX flow** ← Phase 1 작업
  - [x] `POST /api/adaptive/exams/start`
  - [x] `GET /api/adaptive/exams/{session_id}/next-item`
  - [x] `POST /api/adaptive/exams/{session_id}/submit-answer`
  - [x] `GET /api/adaptive/exams/{session_id}/results`
  - [ ] `POST /api/auth/register`
  - [ ] `POST /api/auth/login`
  - [ ] `GET /api/adaptive/pools`
  - [ ] `GET /api/adaptive/exams/history`

### Frontend (0% → 100% in Phase 1)
- [ ] **Landing page** (`/`)
  - Hero section
  - "회원가입" / "로그인" 버튼
- [ ] **Auth pages**
  - `/register` - 회원가입 폼
  - `/login` - 로그인 폼
- [ ] **Student dashboard** (`/student/dashboard`)
  - 시험 목록 (Math, English, Science)
  - 과거 시험 기록
- [ ] **Exam flow**
  - `/student/exams/start` - 시험 시작 확인
  - `/student/exams/{session_id}/item` - 문제 풀이
  - `/student/exams/{session_id}/results` - 결과 화면
- [ ] **History page** (`/student/history`)
  - 과거 시험 목록
  - 각 시험 결과 요약

### Deployment (0% → 100% in Phase 1)
- [ ] **Server setup**
  - 기존 머신 or 새 VM
  - Docker Compose 설치
  - Nginx or Caddy (reverse proxy)
- [ ] **Domain & SSL**
  - dreamseedai.com DNS 설정 (Cloudflare)
  - SSL 인증서 (Let's Encrypt)
  - HTTPS 강제 리다이렉트
- [ ] **Environment variables**
  - Production `.env` 파일
  - Database credentials
  - JWT secret key
  - Redis connection
- [ ] **CI/CD (optional)**
  - GitHub Actions (auto-deploy on push)
  - Blue-green deployment

### Testing & Validation
- [ ] **Manual testing**
  - 전체 UX 흐름 테스트 (회원가입 → 시험 → 결과)
  - 5-10명 베타 테스터 초대
  - 피드백 수집
- [ ] **Performance testing**
  - 5명 동시 접속 (동시 시험)
  - API 응답 시간 < 500ms
  - 시험 진행 중 끊김 없음
- [ ] **Monitoring**
  - Error tracking (Sentry or similar)
  - Basic logging (Docker logs)
  - Health check endpoint (`/health`)

---

## Phase 1.0 vs Phase 2.0 비교

| Feature | Phase 1.0 (Alpha) | Phase 2.0 (Beta) |
|---------|-------------------|------------------|
| **목표** | 5-10명 소규모 베타 | 100-500명 클로즈드 베타 |
| **인증** | JWT 기본 | OAuth2 (Google, GitHub) |
| **역할** | 학생만 | 학생 + 교사 + 학부모 |
| **대시보드** | 간단한 결과 화면 | 상세 분석 리포트 |
| **결제** | 없음 | 구독 플랜 (Stripe) |
| **모니터링** | 기본 로그 | Prometheus + Grafana |
| **트래픽** | 동시 5명 | 동시 100명 |
| **배포** | 단일 서버 + Docker Compose | Kubernetes + Auto-scaling |
| **CAT 기능** | 기본 adaptive | Content balancing, Exposure control |
| **알림** | 없음 | 이메일, SMS, Push |

---

## Phase 1.0 Success Metrics

**정량적 지표:**
- ✅ 베타 테스터 5명 이상 가입
- ✅ 총 시험 완료 20회 이상
- ✅ 평균 API 응답 시간 < 500ms
- ✅ 시스템 uptime > 95% (1주일 기준)
- ✅ Critical bug 0건

**정성적 지표:**
- ✅ 베타 테스터 피드백 수집 (최소 5명)
- ✅ "UX 흐름이 끊기지 않는다" (no blocking issues)
- ✅ "결과가 의미있다" (θ/점수/등급이 납득 가능)
- ✅ "다시 써보고 싶다" (retention signal)

---

## Risks & Mitigation (Alpha 특화)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 베타 테스터 모집 실패 | Medium | High | 가족, 지인 직접 초대 (본인 포함 5명 확보) |
| Frontend 개발 지연 | High | High | 디자인 최소화, 기능 우선 (예쁜 UI는 Phase 2) |
| 서버 다운 | Medium | Medium | Health check + 자동 재시작 (Docker restart policy) |
| CAT 엔진 버그 발견 | Low | Medium | Unit test coverage > 75% (이미 달성) |
| SSL 인증서 만료 | Low | Medium | Let's Encrypt auto-renewal 설정 |

---

## Next Steps (Immediate)

### Week 1 (Nov 25 - Dec 1)
1. **Backend: Authentication API 완성**
   - `POST /api/auth/register`
   - `POST /api/auth/login`
   - JWT 발급 및 검증
   - RBAC middleware

2. **Frontend: 프로젝트 초기화**
   - Next.js or React + Vite 선택
   - Tailwind CSS 설정
   - API client 설정 (axios or fetch)

### Week 2 (Dec 2 - Dec 8)
3. **Frontend: Auth pages 완성**
   - Landing page
   - Register page
   - Login page

4. **Backend: API 통합 테스트**
   - Auth flow E2E test
   - Exam flow E2E test (기존 skip 해제)

### Week 3 (Dec 9 - Dec 15)
5. **Frontend: Exam flow 완성**
   - Student dashboard
   - Exam start page
   - Item display page
   - Results page

6. **Integration: Frontend ↔ Backend 연결**
   - API integration
   - Error handling
   - Loading states

### Week 4 (Dec 16 - Dec 22)
7. **Deployment: dreamseedai.com 설정**
   - Domain DNS
   - SSL certificate
   - Docker Compose on production

8. **Testing & Launch**
   - Manual testing (전체 UX 흐름)
   - Beta tester 초대 (5-10명)
   - Feedback collection

---

## Definition of "Phase 1.0 Complete"

**Official Statement:**
> Phase 1.0 is complete when a beta tester can:
> 1. Visit https://dreamseedai.com
> 2. Register a new account
> 3. Log in
> 4. Start a Math diagnostic test
> 5. Answer 10-20 adaptive questions
> 6. View their results (θ, score, grade)
> 7. Return to dashboard and see test history
> 
> **Without any blocking bugs or broken flows.**

**Detailed Completion Checklist:**
See [PHASE1_ALPHA_CHECKLIST.md](./PHASE1_ALPHA_CHECKLIST.md) for comprehensive acceptance criteria and testing scenarios.

---

## Approval & Sign-off

- [ ] **Product Owner:** Reviewed and approved UX flow
- [ ] **Tech Lead:** Confirmed technical feasibility
- [ ] **Backend Team:** Confirmed API readiness (95% from Phase 0.5)
- [ ] **Frontend Team:** Confirmed 4-week timeline for alpha UI
- [ ] **DevOps:** Confirmed deployment plan

---

**Status:** 📋 **READY TO START**  
**Target Launch:** December 22, 2025 (4 weeks from now)  
**First Beta Tester:** You! 🚀  

---

**End of Phase 1.0 Alpha Launch Plan**
