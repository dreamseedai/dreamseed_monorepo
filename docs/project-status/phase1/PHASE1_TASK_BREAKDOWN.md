# Phase 1.0 Alpha - Detailed Task Breakdown (Jira/Linear Ready)

**Project:** DreamSeed AI Platform  
**Phase:** 1.0 - Alpha Launch (dreamseedai.com)  
**Date:** November 24, 2025  
**Format:** Epic → Story → Task (Copy-paste ready for Jira/Linear/GitHub Issues)  

---

## 🟣 EPIC 1 — Authentication & User Management

**Priority:** 🔴 Critical  
**Estimate:** 5 days  
**Owner:** Backend + Frontend Team  

### Story 1.1 — 회원가입 (Sign-Up)
**Priority:** High  
**Estimate:** 2 days  

- [ ] **Task 1.1.1** — Sign-up API 연결 (`POST /api/auth/register`)
  - API client wrapper 작성
  - 에러 핸들링 (409 Conflict, 400 Bad Request)
  - 성공 응답 파싱
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 1.1.2** — 입력 폼 UI: email, password, name
  - Form component 생성 (`components/auth/RegisterForm.tsx`)
  - Input validation (client-side)
  - Submit button state management
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 1.1.3** — Validation (email format, password rules)
  - Email regex validation
  - Password: 최소 8자, 대문자, 숫자, 특수문자
  - Real-time validation feedback
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 1.1.4** — 성공 시 자동 로그인 or 로그인 페이지 이동
  - 회원가입 성공 후 JWT 저장
  - Dashboard redirect
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 1.1.5** — 오류 처리 UI (중복 이메일 등)
  - Toast notification or inline error
  - 409 Conflict → "이미 존재하는 이메일입니다"
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

### Story 1.2 — 로그인 (Login)
**Priority:** High  
**Estimate:** 2 days  

- [ ] **Task 1.2.1** — Login API 연결 (`POST /api/auth/login`)
  - API client method 작성
  - 에러 핸들링 (401 Unauthorized, 400 Bad Request)
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 1.2.2** — JWT 저장 (HTTP-only cookie or local storage 결정)
  - **Decision:** localStorage for alpha (simple), httpOnly cookie for production
  - Token 저장 utility function
  - Token 만료 처리
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 1.2.3** — 로그인 성공 → Dashboard redirect
  - `/dashboard` 경로로 이동
  - User context 설정
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 1.2.4** — 로그인 실패 UI
  - 401 → "이메일 또는 비밀번호가 잘못되었습니다"
  - Toast notification
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

### Story 1.3 — 로그아웃
**Priority:** Medium  
**Estimate:** 0.5 days  

- [ ] **Task 1.3.1** — Logout endpoint 연동
  - `POST /api/auth/logout` (optional for alpha)
  - Or client-side token deletion
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 1.3.2** — 토큰 삭제 & redirect
  - localStorage.removeItem('token')
  - Redirect to `/login`
  - Clear user context
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

### Story 1.4 — Role-Based Access Control
**Priority:** High  
**Estimate:** 1 day  

- [ ] **Task 1.4.1** — `/dashboard` / `/exam/*` 보호 라우트 설정
  - Protected route wrapper component
  - Token 존재 여부 확인
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 1.4.2** — Unauthenticated 접근 → 로그인 페이지
  - Redirect to `/login?redirect=/dashboard`
  - 로그인 후 원래 페이지로 복귀
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

---

## 🟢 EPIC 2 — Landing Page & Onboarding

**Priority:** 🔴 Critical  
**Estimate:** 2 days  
**Owner:** Frontend Team  

### Story 2.1 — Landing Page
**Priority:** High  
**Estimate:** 1 day  

- [ ] **Task 2.1.1** — Header / Logo / CTA(시작하기)
  - Navigation bar with logo
  - "시작하기" button → `/register`
  - "로그인" button → `/login`
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 2.1.2** — Footer 최소 구성
  - Copyright notice
  - "알파 버전" badge
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 2.1.3** — dreamseedai.com branding 반영
  - Logo upload
  - Color scheme (Tailwind config)
  - Typography
  - **Assignee:** Frontend Dev + Designer
  - **Estimate:** 2 hours

---

### Story 2.2 — Onboarding (Alpha)
**Priority:** Medium  
**Estimate:** 1 day  

- [ ] **Task 2.2.1** — Test 영역 선택 (Math 활성 / English & Science disabled)
  - Subject selection card UI
  - Math card → `/exam/start?subject=math`
  - English/Science → disabled state
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 2.2.2** — "Coming soon" 배지 표시
  - Badge component
  - Tooltip: "Phase 1.5에 추가 예정"
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

## 🔵 EPIC 3 — Math Exam Flow (CAT Engine 연결)

**Priority:** 🔴 Critical  
**Estimate:** 6 days  
**Owner:** Frontend Team  

### Story 3.1 — 시험 시작
**Priority:** High  
**Estimate:** 1 day  

- [ ] **Task 3.1.1** — Intro 화면 UI
  - Exam intro card
  - "Math 진단 테스트" 제목
  - 예상 시간: 10-20분
  - 예상 문항 수: 10-20개
  - "시작하기" button
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 3.1.2** — API 연결: `POST /api/adaptive/exams/start`
  - Request: `{ "pool_id": <math_pool_id> }`
  - Response: `{ "session_id": "uuid", "initial_theta": 0.0 }`
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 3.1.3** — session_id / 첫 문항 ID 저장
  - Store in React state or context
  - Fetch first item: `GET /api/adaptive/exams/{session_id}/next-item`
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

---

### Story 3.2 — 문항 표시
**Priority:** High  
**Estimate:** 3 days  

- [ ] **Task 3.2.1** — Question card UI
  - Component: `QuestionCard.tsx`
  - Display: question number, text, progress bar
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 3.2.2** — 보기 4개 렌더링
  - Component: `OptionButton.tsx`
  - Radio button or button group
  - Selected state styling
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 3.2.3** — `/api/adaptive/exams/{session_id}/submit-answer` 호출
  - Request: `{ "item_id": 123, "choice_id": 456 }`
  - Response: `{ "is_correct": true, "new_theta": 0.5, "se": 0.4 }`
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 3.2.4** — `/api/adaptive/exams/{session_id}/next-item` 호출
  - Fetch next item after submit
  - Loading state (skeleton or spinner)
  - Update progress bar
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

---

### Story 3.3 — 종료 조건/에러 처리
**Priority:** High  
**Estimate:** 2 days  

- [ ] **Task 3.3.1** — `finished=true` 상태 감지
  - Check `/next-item` response for `{ "finished": true }`
  - Redirect to `/exam/result?session_id={id}`
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 3.3.2** — 네트워크 오류 시 fallback
  - Retry logic (3 attempts)
  - Error toast: "네트워크 오류가 발생했습니다"
  - "다시 시도" button
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

---

## 🟡 EPIC 4 — Results & Dashboard

**Priority:** 🟠 High  
**Estimate:** 3 days  
**Owner:** Frontend Team  

### Story 4.1 — Result Page
**Priority:** High  
**Estimate:** 2 days  

- [ ] **Task 4.1.1** — θ 기반 score 변환 표시
  - API: `GET /api/adaptive/exams/{session_id}/results`
  - Response: `{ "theta": 0.75, "score": 67, "grade": "B", "level": "Intermediate" }`
  - Display score (0-100) prominently
  - **Assignee:** Frontend Dev
  - **Estimate:** 2 hours

- [ ] **Task 4.1.2** — 레벨 (Basic/Intermediate/Advanced)
  - Badge component for level
  - Color coding (green/yellow/red)
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 4.1.3** — 간단한 해석 텍스트
  - Feedback text from API
  - "현재 수준은 중급이며, 함수 문제를 연습하면 향상 가능합니다."
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

- [ ] **Task 4.1.4** — "다시 테스트하기" 버튼
  - Button → `/exam/start`
  - "대시보드로 돌아가기" button → `/dashboard`
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

### Story 4.2 — Student Dashboard
**Priority:** Medium  
**Estimate:** 1 day  

- [ ] **Task 4.2.1** — 최근 테스트 기록 표시
  - API: `GET /api/adaptive/exams/history`
  - Display: date, subject, score, level
  - Limit: 최근 3개
  - **Assignee:** Frontend Dev
  - **Estimate:** 3 hours

- [ ] **Task 4.2.2** — 기록 없을 때 "기록 없음" 표시
  - Empty state component
  - "첫 진단 시작하기" button → `/dashboard` (subject selection)
  - **Assignee:** Frontend Dev
  - **Estimate:** 1 hour

---

## 🟠 EPIC 5 — Deployment & Domain

**Priority:** 🔴 Critical  
**Estimate:** 3 days  
**Owner:** DevOps + Backend Team  

- [ ] **Task 5.1** — Backend Docker Compose 서버 배포
  - Deploy `docker-compose.phase0.5.yml` to production server
  - Configure production `.env` file
  - Verify all services healthy
  - **Assignee:** DevOps
  - **Estimate:** 1 day

- [ ] **Task 5.2** — API gateway 설정 (CORS, HTTPS)
  - Configure CORS (allow dreamseedai.com)
  - Set up reverse proxy (Nginx or Caddy)
  - SSL certificate (Let's Encrypt)
  - **Assignee:** DevOps
  - **Estimate:** 1 day

- [ ] **Task 5.3** — Cloudflare SSL/Proxy 활성화
  - Configure Cloudflare DNS
  - A record: dreamseedai.com → server IP
  - Enable HTTPS (Full or Full Strict)
  - **Assignee:** DevOps
  - **Estimate:** 0.5 day

- [ ] **Task 5.4** — dreamseedai.com FE 배포 (Vercel or Docker)
  - **Option A:** Deploy to Vercel (recommended for Next.js)
  - **Option B:** Docker + Nginx on same server
  - Configure API base URL (environment variable)
  - **Assignee:** DevOps + Frontend
  - **Estimate:** 0.5 day

---

## 🟤 EPIC 6 — Observability (Phase 1.5로 이동)

**Priority:** 🟢 Low (Deferred)  
**Estimate:** 3 days (Phase 1B)  

- [ ] Prometheus minimal endpoint (`/metrics`)
- [ ] Grafana dashboard base (API response time, error rate)
- [ ] Error log aggregator (Sentry or similar)

**Note:** 알파 버전에서는 Docker logs로 충분. Phase 1B에서 구현.

---

## 📊 Task Summary

| Epic | Stories | Tasks | Total Estimate |
|------|---------|-------|----------------|
| 1. Authentication | 4 | 11 | 5 days |
| 2. Landing & Onboarding | 2 | 4 | 2 days |
| 3. Exam Flow | 3 | 9 | 6 days |
| 4. Results & Dashboard | 2 | 5 | 3 days |
| 5. Deployment | 1 | 4 | 3 days |
| **Total** | **12** | **33** | **19 days** |

**With parallelization (Frontend + Backend + DevOps):**
- Week 1 (5 days): Epic 1 (Auth)
- Week 2 (5 days): Epic 2-3 (Landing + Exam Flow start)
- Week 3 (5 days): Epic 3-4 (Exam Flow complete + Results)
- Week 4 (5 days): Epic 5 (Deployment + Testing)

**Total Calendar Time:** 4 weeks (28 days)

---

## 🎯 Priority Matrix

### Must Have (P0) - Blocking Alpha Launch
- ✅ Epic 1: Authentication (all tasks)
- ✅ Epic 2: Landing Page (Story 2.1)
- ✅ Epic 3: Exam Flow (all tasks)
- ✅ Epic 4: Results (Story 4.1)
- ✅ Epic 5: Deployment (all tasks)

### Should Have (P1) - Nice to Have
- Epic 2: Onboarding (Story 2.2)
- Epic 4: Dashboard (Story 4.2)

### Could Have (P2) - Phase 1B
- Epic 6: Observability

---

## 📝 Notes for Jira/Linear Setup

### Epic Template
```
Title: [Epic 1] Authentication & User Management
Description: Implement JWT-based authentication with sign-up, login, logout
Priority: Critical
Estimate: 5 days
Owner: Backend + Frontend Team
```

### Story Template
```
Title: [Story 1.1] 회원가입 (Sign-Up)
Description: User registration with email, password, name
Acceptance Criteria:
- User can submit registration form
- Email validation works
- Password validation works
- Success → auto-login or redirect to login
- Error → show error message
Estimate: 2 days
```

### Task Template
```
Title: [Task 1.1.1] Sign-up API 연결
Description: Connect frontend to POST /api/auth/register
Acceptance Criteria:
- API client wrapper created
- Error handling (409, 400)
- Success response parsed
Estimate: 2 hours
Assignee: Frontend Dev
```

---

**Status:** 📋 **READY FOR SPRINT PLANNING**  
**Next Step:** Import to Jira/Linear/GitHub Projects  
**Related Docs:** [PHASE1_ALPHA_CHECKLIST.md](./PHASE1_ALPHA_CHECKLIST.md)  

---

**End of Phase 1.0 Task Breakdown**
