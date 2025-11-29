# Phase 1.0 Alpha Completion Checklist

**Project:** DreamSeed AI Platform  
**Phase:** 1.0 - Alpha Launch (dreamseedai.com)  
**Date:** November 24, 2025  
**Status:** 📋 **PLANNING**  

---

## Definition of "Phase 1 Complete"

> **Phase 1.0 = dreamseedai.com 알파 버전 학생 진단 UX 완성**
> 
> A beta tester (student) can visit https://dreamseedai.com, register, log in, 
> complete a Math diagnostic test, view results, and return to dashboard 
> **without any blocking bugs or broken flows**.

---

## Student UX Scenario (Reference Flow)

### Part 1: 첫 방문 & 진입

**Step 1-3: Landing Page**
1. 학생이 브라우저에서 `https://dreamseedai.com` 입력
2. 심플한 랜딩 페이지가 뜬다:
   - 로고 / 서비스 이름
   - 짧은 설명: "AI 기반 능력/실력 진단 테스트 (알파 버전)"
   - 두 개의 버튼:
     * **[시작하기 (회원가입)]**
     * **[로그인]**
3. 학생이 **[시작하기]**를 클릭한다.

---

### Part 2: 회원가입 & 로그인

**Step 4-6: Authentication**
4. 간단한 회원가입 폼:
   - 이메일
   - 비밀번호
   - 이름 (닉네임 정도)
   - 동의 체크박스 (이용 약관 / 알파 버전 안내)
5. 회원가입 성공 → 자동으로 로그인 처리되거나, "로그인 화면으로 이동"
6. 로그인 후, 상단에:
   - "환영합니다, OOO님"
   - **[진단 테스트 시작하기]** 버튼이 보인다.

*(기존 계정이 있는 학생은 처음부터 [로그인]을 눌러 동일한 화면으로 진입)*

---

### Part 3: 간단 온보딩 (선택 사항, 최소 버전)

**Step 7-8: Test Selection**
7. **[진단 테스트 시작하기]** 클릭 시, 간단한 선택 화면:
   - "어떤 영역을 진단해 볼까요?"
     * **Math**
     * **English**
     * **Science**
   - 향후 확장을 고려해 "나중에 더 추가될 예정입니다" 정도 안내
8. 학생이 예를 들어 **Math**를 선택하고 **[진단 시작]** 버튼을 누른다.

---

### Part 4: 시험 소개 화면

**Step 9-10: Pre-Test Screen**
9. 시험 시작 전 간단한 안내 화면:
   - "Math 진단 테스트 (알파 버전)"
   - 예상 문항 수: **10~20문항** (CAT이 적응적으로 조정)
   - 예상 소요 시간: **약 10~20분**
   - "중간에 나가면 결과가 저장되지 않을 수 있습니다."
   - **[시작하기]** 버튼
10. 학생이 **[시작하기]**를 누르면 백엔드에서:
    - `POST /api/adaptive/exams/start` 호출
    - `exam_session_id`, 초기 θ, Redis state 생성

---

### Part 5: 문제 풀이 화면 (CAT 진행)

**Step 11-14: Item Display & Submission Loop**
11. **첫 문제 화면:**
    - 상단: "문항 X / ?" (전체 문항 수는 숨기거나 대략적인 progress bar)
    - 중앙: 질문 텍스트 (Math 문제)
    - 하단: 4지선다 보기 버튼 (A/B/C/D)
    - 오른쪽/상단: "진행도 바" 또는 간단한 인디케이터
    - 하단: **[다음]** (답안을 고른 뒤 활성화)

12. 학생이 보기 하나를 선택 → 내부적으로:
    - `POST /api/adaptive/exams/{session_id}/submit-answer` 호출
      - Input: `session_id`, `item_id`, 선택한 `choice_id`
    - 서버에서 θ 업데이트, SE 계산, 종료 조건 확인
    - `GET /api/adaptive/exams/{session_id}/next-item`로 다음 문항 id 선택

13. 프론트엔드는 응답을 받아 다음 문항을 화면에 표시

14. **이 과정을 여러 번 반복:**
    - 난이도/정보량에 따라 문제 난이도가 조정됨
    - `SE < 목표값` 또는 `최대 문항 수` 도달 시 종료 플래그 설정

---

### Part 6: 시험 종료 & 결과 화면

**Step 15-17: Results Display**
15. 마지막 문항까지 풀어 **"테스트 종료 조건"**이 만족되면:
    - 백엔드가 `/submit-answer` 또는 `/status` 응답에서 `"finished": true`를 반환
    - 프론트는 문제 화면 대신 **결과 요약 화면**으로 전환

16. **결과 화면 내용 (알파 버전 기준 최소):**
    - "Math 진단 결과"
    - 추정 실력 θ (숫자는 노출 여부 선택 가능, 내부용일 수도)
    - **학생에게 보이는 형태:**
      * **0–100 점수**
      * **난이도 레벨** (예: Basic / Intermediate / Advanced)
      * **간단한 설명:** "현재 수준은 ~~~이며, 향후 추천: ~~" (간단 텍스트)
    - **예시:**
      * 총 14문항 응답
      * 예상 상위 23% 수준
      * "다음 단계: 함수/그래프 문제를 중점적으로 학습하면 좋겠습니다."

17. **하단 버튼:**
    - **[다시 테스트하기]** (동일 영역 재테스트 or 다른 영역)
    - **[대시보드로 돌아가기]** (학생 메인 화면)

---

### Part 7: 학생 마이페이지 (간단 버전)

**Step 18-19: Dashboard & History**
18. 대시보드 또는 마이페이지에 **최소한의 기록:**
    - 최근 테스트 기록 1줄:
      * 날짜, 영역(Math), 점수, 레벨
    - "최근 기록 3개" 정도만 보여줘도 충분

19. 여기서 다시:
    - **[새 진단 시작]**
    - **[로그아웃]**
    - 까지 흐르면, **알파 버전 목표 UX는 충분히 달성**입니다.

---

## Phase 1 Completion Checklist

### A. 도메인 & 접속 🌐

- [ ] **dreamseedai.com 도메인으로 HTTPS 접속 가능**
  - Cloudflare DNS 설정 완료
  - SSL 인증서 적용 (Let's Encrypt or Cloudflare)
  - HTTP → HTTPS 자동 리다이렉트

- [ ] **기본 랜딩 페이지 (`/`)**
  - 서비스 한 줄 소개 표시
  - **[시작하기]** 버튼 노출
  - **[로그인]** 버튼 노출
  - 반응형 디자인 (모바일 접속 가능)

---

### B. 인증 / 계정 (Auth & User Flow) 🔐

- [ ] **회원가입 기능 (`POST /api/auth/register`)**
  - 이메일 + 비밀번호 기반 회원가입 동작
  - 이메일 중복 체크
  - 비밀번호 강도 검증 (최소 8자)
  - 회원가입 성공 시 자동 로그인 또는 로그인 페이지 리다이렉트

- [ ] **로그인 기능 (`POST /api/auth/login`)**
  - 이메일 + 비밀번호 인증
  - JWT 토큰 발급
  - 토큰을 localStorage 또는 httpOnly cookie에 저장

- [ ] **로그아웃 기능**
  - 로그아웃 버튼 클릭 시 토큰 삭제
  - 로그인 페이지로 리다이렉트

- [ ] **로그인 후 학생용 대시보드로 이동**
  - `/student/dashboard` 또는 `/dashboard` 경로
  - "환영합니다, OOO님" 표시

- [ ] **최소 권한 체계**
  - `student` 역할로 보호된 API만 접근 가능
  - 로그인하지 않은 상태에서 시험 관련 페이지 접근 시 로그인 페이지로 리다이렉트
  - Backend middleware: `@require_role("student")` 또는 유사 메커니즘

---

### C. 진단 테스트 시작 플로우 🚀

- [ ] **[진단 테스트 시작하기] 버튼**
  - 대시보드에서 버튼 클릭 시 영역 선택 화면으로 진입

- [ ] **영역 선택 화면 (`/student/tests` or `/select-subject`)**
  - Math / English / Science 중 하나 선택 가능
  - **알파 버전:** 최소 1개(Math)만 실제로 동작해도 OK
  - 문서에 "English/Science는 Phase 1.5 또는 Phase 2에 추가 예정" 명시

- [ ] **시험 소개 화면 (`/student/exams/start`)**
  - 예상 시간/문항수 안내 표시
  - 알파 버전 안내 문구
  - **[시작하기]** 버튼 정상 동작

- [ ] **`POST /api/adaptive/exams/start` 호출 성공**
  - `exam_session_id` 생성
  - Redis/DB에 state 저장 (initial θ, SE, items_seen)
  - Frontend로 session_id 반환

---

### D. CAT 시험 진행 (문항 화면 & 로직) 📝

- [ ] **첫 문항 로딩 (`GET /api/adaptive/exams/{session_id}/next-item`)**
  - 질문 텍스트 / 4개 보기 UI 렌더링
  - Progress bar 또는 "문항 1 / ?" 표시

- [ ] **학생이 답안 선택**
  - 라디오 버튼 또는 버튼 UI로 선택
  - 선택 시 **[다음]** 버튼 활성화

- [ ] **답변 제출 (`POST /api/adaptive/exams/{session_id}/submit-answer`)**
  - Input: `item_id`, `choice_id`
  - Backend: θ 업데이트 (Newton-Raphson MLE)
  - Backend: SE 계산
  - Backend: 종료 조건 확인 (SE < 0.3 or max items)

- [ ] **다음 문항 로딩 반복**
  - Frontend가 다음 문항을 정상 렌더링
  - Progress bar 업데이트 (문항 2, 3, 4, ...)

- [ ] **오류 처리**
  - 서버 에러 시 "다시 시도" 또는 "테스트 중단 안내" 표시
  - Network timeout 처리 (5초 이상 응답 없으면 재시도 UI)

- [ ] **종료 조건**
  - SE 기준 또는 최대 문항 수 기준으로 시험 종료 플래그가 내려옴
  - `finished: true` 응답 시 더 이상 새로운 문항 요청을 하지 않음
  - 결과 화면으로 자동 전환

---

### E. 결과 화면 (Result Page) 📊

- [ ] **시험 종료 시 결과 페이지로 자동 이동**
  - URL: `/student/exams/{session_id}/results`

- [ ] **결과 페이지에 아래 항목 표시:**
  - **영역 이름** (예: "Math 진단 결과")
  - **최종 점수** (0–100 스케일)
  - **레벨/등급** (예: Basic / Intermediate / Advanced 또는 A-F)
  - **간단한 해석 텍스트** (1–3줄)
    - 예: "현재 수준은 중급이며, 함수 문제를 연습하면 향상 가능합니다."
  - **문항 통계 (선택 사항):**
    - 총 문항 수, 정답 수, 정답률
    - 난이도 분포 (Easy: X개, Medium: Y개, Hard: Z개)

- [ ] **버튼:**
  - **[다시 테스트하기]** (동일 영역 재시작 or 다른 영역 선택)
  - **[대시보드로 돌아가기]**

- [ ] **API 호출 (`GET /api/adaptive/exams/{session_id}/results`)**
  - Output: `theta`, `score`, `grade`, `level`, `feedback_text`

---

### F. 간단한 기록/대시보드 📋

- [ ] **학생 대시보드에서 최근 테스트 표시**
  - 최근 테스트 1개 이상 표시:
    * 날짜 (YYYY-MM-DD HH:mm)
    * 영역 (Math, English, Science)
    * 점수 (0-100)
    * 레벨 (Basic/Intermediate/Advanced)
  - 카드 또는 테이블 형태로 렌더링

- [ ] **기록이 없는 신규 계정 처리**
  - "아직 테스트 기록이 없습니다" 메시지 표시
  - **[첫 진단 시작하기]** 버튼 제공

- [ ] **API 호출 (`GET /api/adaptive/exams/history`)**
  - User's past exams sorted by date (최신순)
  - Limit: 최근 3개 (알파 버전)

---

### G. 백엔드 & 인프라 측 요구 조건 🛠️

- [ ] **Docker Compose로 전체 스택 구동**
  - `docker compose up -d` 한 줄로 실행
  - Services: PostgreSQL, Redis, Backend, Frontend (optional: nginx)
  - All services healthy (green status)

- [ ] **CAT/IRT 엔진 동작 확인**
  - θ 업데이트 로직 (Newton-Raphson MLE)
  - Fisher Information 계산
  - 종료 조건 (SE < 0.3 or max 20 items)
  - Item selection (Fisher Information 기반 정렬)

- [ ] **Database 상태**
  - PostgreSQL 30 tables created
  - Seed data: 120 items, 480 choices, 3 pools
  - `exam_sessions`, `attempts`, `students` tables functional

- [ ] **Redis 상태**
  - Adaptive state store working
  - TTL: 3600s (1 hour)
  - JSON serialization (theta, se, items_seen, responses)

- [ ] **최소 모니터링**
  - 에러 로그가 파일 또는 콘솔에 기록됨
  - Docker logs accessible: `docker compose logs -f backend`
  - Health check endpoint: `GET /health` returns 200

- [ ] **AI Requests 로깅 (선택 사항)**
  - `ai_requests` 테이블에 기본적인 AI 호출 로그 저장
  - Columns: user_id, model, prompt_tokens, completion_tokens, cost

---

### H. 제외/Defer (Phase 1 이후로 넘기는 항목) ⏭️

**다음 항목들은 Phase 1 알파 완료 기준에서 제외되며, 문서에 명시합니다:**

- [ ] ❌ **완전 자동화된 E2E 테스트** (pytest + real infra)
  - **Defer to:** Phase 1B (Week 5-6)
  - **Rationale:** 알파는 수동 테스트로 충분, E2E 안정화는 이후 단계

- [ ] ❌ **고급 CAT 기능**
  - Exposure control (문항 노출 제어)
  - Content balancing (영역별 문항 비율 조정)
  - Multi-dimensional IRT (다차원 능력 추정)
  - **Defer to:** Phase 1B (Week 5-6) or Phase 2

- [ ] ❌ **풀스케일 모니터링**
  - Prometheus + Grafana dashboards
  - Alerting (Slack, Email)
  - Performance metrics (p50, p95, p99)
  - **Defer to:** Phase 1B (Week 7-8)

- [ ] ❌ **결제/구독 시스템**
  - Stripe integration
  - Subscription plans (월간/연간)
  - Free trial management
  - **Defer to:** Phase 2

- [ ] ❌ **역할별 대시보드**
  - Teacher dashboard (학생 진도 모니터링)
  - Parent dashboard (자녀 성적 조회)
  - Admin dashboard (시스템 관리)
  - **Defer to:** Phase 2

- [ ] ❌ **OAuth2 인증**
  - Google login
  - GitHub login
  - Account linking
  - **Defer to:** Phase 1B (optional) or Phase 2

---

## Alpha Launch Strategy: Math-First Approach 🎯

### Phase 1A: Math Only (Week 1-4)
**Goal:** Prove the concept with one subject

- ✅ **Math 진단 테스트 100% 완성**
  - 120 items (40 Math + 40 English + 40 Science → Math 40만 활성화)
  - Full UX flow working
  - Beta tester validation (5-10명)

- ⏸️ **English/Science = "Coming Soon"**
  - UI에 버튼 보이지만 클릭 시 "준비 중입니다" 메시지
  - 또는 아예 숨기고 Math만 노출

### Phase 1.5: Multi-Subject Expansion (Week 5-6, Optional)
**Goal:** Expand to all 3 subjects

- ✅ **English 활성화** (40 items 이미 준비됨)
- ✅ **Science 활성화** (40 items 이미 준비됨)
- ✅ **Cross-subject comparison** (학생이 3개 영역 모두 테스트 가능)

**Decision Point:**
- Math 알파 피드백이 긍정적 → 바로 Phase 1.5 진행
- Math 알파에서 큰 문제 발견 → Phase 1.5 연기, Phase 1A 개선 우선

---

## Success Metrics (Phase 1 완료 기준)

### Quantitative Metrics
- ✅ **5명 이상의 베타 테스터 가입**
- ✅ **총 20회 이상의 시험 완료** (Math 진단)
- ✅ **평균 API 응답 시간 < 500ms**
  - `POST /api/adaptive/exams/start`: < 200ms
  - `GET /api/adaptive/exams/{session_id}/next-item`: < 300ms
  - `POST /api/adaptive/exams/{session_id}/submit-answer`: < 400ms
- ✅ **시스템 uptime > 95%** (1주일 기준)
- ✅ **Critical bug 0건** (시험 진행 불가 또는 결과 표시 실패)

### Qualitative Metrics
- ✅ **베타 테스터 피드백 수집** (최소 5명)
  - Google Form 또는 간단한 설문
  - "UX 흐름이 끊기지 않았나요?"
  - "결과가 의미있었나요?"
  - "다시 써보고 싶나요?"
- ✅ **"UX 흐름이 끊기지 않는다"** (no blocking issues)
- ✅ **"결과가 의미있다"** (θ/점수/등급이 납득 가능)
- ✅ **"다시 써보고 싶다"** (retention signal)

---

## Definition of Done (Official)

**Phase 1.0 is COMPLETE when:**

> ✅ A beta tester can complete the following scenario **without any blocking bugs:**
> 
> 1. Visit https://dreamseedai.com
> 2. Click **[시작하기]** → Register account (email, password, name)
> 3. Log in automatically or manually
> 4. Click **[진단 테스트 시작하기]** → Select **Math**
> 5. Click **[시작하기]** → See first question
> 6. Answer 10-20 adaptive questions (progress bar updates)
> 7. Reach test end → Auto-redirect to results page
> 8. View results: score (0-100), level (Basic/Intermediate/Advanced), feedback text
> 9. Click **[대시보드로 돌아가기]** → See test history (1 record)
> 10. Click **[로그아웃]** → Return to landing page
> 
> **AND:**
> - ✅ 5+ beta testers have completed this flow
> - ✅ Feedback collected from all testers
> - ✅ System uptime > 95% (1 week)
> - ✅ No critical bugs reported

---

## Approval & Sign-off

- [ ] **Product Owner:** Reviewed UX scenario and checklist
- [ ] **Tech Lead:** Confirmed technical feasibility
- [ ] **Backend Team:** Confirmed API readiness (95% from Phase 0.5)
- [ ] **Frontend Team:** Committed to 4-week timeline
- [ ] **DevOps:** Confirmed deployment plan for dreamseedai.com
- [ ] **QA/Testing:** Committed to manual testing with 5-10 beta testers

---

**Status:** 📋 **READY FOR EXECUTION**  
**Target Completion:** December 22, 2025 (4 weeks from now)  
**First Beta Test:** December 23, 2025 🚀  

---

**Related Documents:**
- [Phase 1.0 Alpha Launch Plan](./PHASE1_ALPHA_LAUNCH_PLAN.md) - Detailed UX flow with API endpoints
- [Phase 1.0 Initial Backlog](./PHASE1_INITIAL_BACKLOG.md) - Epic breakdown and estimates
- [Phase 0.5 Completion Report](../phase0.5/PHASE0.5_COMPLETION_REPORT.md) - Backend readiness

---

**End of Phase 1.0 Alpha Completion Checklist**
