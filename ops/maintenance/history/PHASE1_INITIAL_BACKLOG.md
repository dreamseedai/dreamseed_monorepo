# Phase 1.0 - Initial Backlog

**Project:** DreamSeed AI Platform  
**Phase:** 1.0 - Alpha Launch (dreamseedai.com)  
**Target Start:** November 25, 2025  
**Target Duration:** 4 weeks (Alpha) + 4 weeks (Hardening) = 8 weeks total  
**Status:** 📋 **PLANNING**  

> **⚠️ IMPORTANT: Phase 1.0 재정의**  
> 기존: "Authentication, Security & Advanced Features" (기술 중심)  
> 변경: "dreamseedai.com 알파 런칭" (실사용 시나리오 중심)  
> 
> **상세 알파 런칭 계획:** [PHASE1_ALPHA_LAUNCH_PLAN.md](./PHASE1_ALPHA_LAUNCH_PLAN.md)

---

## Phase 1.0 Objectives (재정의)

**Primary Goal:**
✅ **dreamseedai.com에서 실질적으로 써볼 수 있는 알파 버전**
- 학생이 직접 접속해서 시험을 보고 결과를 볼 수 있는 최소 UX 흐름
- 소규모 베타 테스트 가능 (본인 + 가족 + 지인 5-10명)
- 실제 피드백을 받아서 Phase 2 설계에 반영

**Secondary Goals:**
1. Implement core authentication & authorization (JWT, RBAC)
2. Build minimal frontend (landing, auth, exam flow, results)
3. Deploy to dreamseedai.com with SSL
4. Stabilize E2E testing infrastructure
5. Collect beta tester feedback

**Success Criteria:**
- ✅ 베타 테스터가 https://dreamseedai.com 접속 가능
- ✅ 회원가입, 로그인, 시험 진행, 결과 확인 전체 흐름 작동
- ✅ 5명 이상의 베타 테스터로부터 피드백 수집
- ✅ 시스템 uptime > 95% (1주일 기준)
- ✅ Critical bug 0건

---

## Epic 1: Authentication & Authorization (Weeks 1-2)

**Priority:** 🔴 Critical  
**Goal:** Secure all API endpoints with JWT-based authentication

### User Stories

#### 1.1 User Registration & Login
**As a** new user  
**I want to** register an account and log in  
**So that** I can access the platform securely

**Acceptance Criteria:**
- [ ] POST /api/auth/register endpoint
  - Email validation (unique, valid format)
  - Password hashing (bcrypt, cost factor 12)
  - Return user ID + JWT access token
- [ ] POST /api/auth/login endpoint
  - Email + password authentication
  - Return access token (15 min TTL) + refresh token (7 day TTL)
  - Failed login tracking (max 5 attempts, 15 min lockout)
- [ ] POST /api/auth/refresh endpoint
  - Exchange refresh token for new access token
  - Rotate refresh token on use

**Technical Tasks:**
- [ ] Install FastAPI-Users or implement custom JWT logic
- [ ] Create auth router (`backend/app/api/routers/auth.py`)
- [ ] Add password strength validation (min 8 chars, uppercase, number, special)
- [ ] Implement token blacklist (Redis-based)
- [ ] Write unit tests for auth flows

**Estimate:** 3 days  
**Dependencies:** None  

---

#### 1.2 Role-Based Access Control (RBAC)
**As a** system administrator  
**I want to** enforce role-based permissions  
**So that** users can only access authorized resources

**Roles:**
- **Student:** Access own exams, attempts, scores
- **Teacher:** Access own students' data, create exams
- **Parent:** Access own children's data (read-only)
- **Admin:** Full access to all resources

**Acceptance Criteria:**
- [ ] Role assignment during user creation
- [ ] Middleware to check permissions (`require_role` decorator)
- [ ] API endpoints protected with role checks
  - `/api/adaptive/*` → Student, Teacher, Admin
  - `/api/admin/*` → Admin only
  - `/api/teacher/*` → Teacher, Admin
- [ ] Forbidden (403) response for unauthorized access

**Technical Tasks:**
- [ ] Create `Role` enum (`backend/app/models/enums.py`)
- [ ] Add `role` column to `users` table (Alembic migration)
- [ ] Implement `get_current_user` dependency with role check
- [ ] Create role-based decorators (`@require_role("admin")`)
- [ ] Write RBAC integration tests

**Estimate:** 2 days  
**Dependencies:** 1.1 (User Registration)  

---

#### 1.3 Password Reset Flow
**As a** user who forgot their password  
**I want to** reset it via email  
**So that** I can regain access to my account

**Acceptance Criteria:**
- [ ] POST /api/auth/forgot-password endpoint
  - Send reset email with secure token (6-digit code or UUID)
  - Token expires in 1 hour
- [ ] POST /api/auth/reset-password endpoint
  - Validate token
  - Update password (re-hash)
  - Invalidate all existing sessions

**Technical Tasks:**
- [ ] Set up SMTP configuration (environment variables)
- [ ] Create email template for password reset
- [ ] Generate secure reset tokens (UUID + timestamp)
- [ ] Store tokens in Redis with TTL (1 hour)
- [ ] Write email sending service (`backend/app/services/email.py`)

**Estimate:** 2 days  
**Dependencies:** 1.1 (User Registration)  

---

#### 1.4 OAuth2 Integration (Optional)
**As a** user  
**I want to** log in with Google/GitHub  
**So that** I don't need to remember another password

**Acceptance Criteria:**
- [ ] Google OAuth2 flow
  - Redirect to Google consent screen
  - Exchange auth code for tokens
  - Create or link user account
- [ ] GitHub OAuth2 flow (same as Google)
- [ ] Link external accounts to existing users

**Technical Tasks:**
- [ ] Install `authlib` library
- [ ] Configure OAuth2 clients (Google, GitHub)
- [ ] Create `/api/auth/oauth/{provider}` endpoints
- [ ] Handle account linking conflicts
- [ ] Write OAuth2 integration tests

**Estimate:** 3 days  
**Dependencies:** 1.1 (User Registration)  
**Priority:** Low (defer if time constrained)  

---

### Epic 1 Summary
**Total Estimate:** 8-10 days  
**Target Completion:** Week 2  
**Blockers:** None  

---

## Epic 2: Security Hardening (Weeks 5-6)

**Priority:** 🟠 High  
**Goal:** Implement defense-in-depth security layers

### User Stories

#### 2.1 PostgreSQL Row-Level Security (RLS)
**As a** security engineer  
**I want to** enforce data isolation at the database level  
**So that** application bugs don't leak data across users

**Scope:**
- Student data isolation (students can only see own records)
- Organization data isolation (teachers see only own org)
- Role-based RLS policies (admin bypass)

**Acceptance Criteria:**
- [ ] Enable RLS on sensitive tables
  - `students`, `exam_sessions`, `attempts`
  - `classes`, `student_classroom`
- [ ] Create RLS policies
  - `students_isolation_policy`: `student.user_id = current_user_id()`
  - `org_isolation_policy`: `class.org_id = current_user_org_id()`
  - `admin_bypass_policy`: `current_user_role() = 'admin'`
- [ ] Test RLS enforcement
  - Student cannot query other students' data
  - Teacher cannot access other orgs' data
  - Admin can see all data

**Technical Tasks:**
- [ ] Write Alembic migration to enable RLS
- [ ] Create helper functions: `current_user_id()`, `current_user_org_id()`, `current_user_role()`
- [ ] Apply policies to each table
- [ ] Write RLS integration tests
- [ ] Document RLS setup in `docs/security/RLS_GUIDE.md`

**Estimate:** 3 days  
**Dependencies:** 1.2 (RBAC)  

---

#### 2.2 API Rate Limiting
**As a** platform operator  
**I want to** prevent API abuse  
**So that** the system remains available for legitimate users

**Rate Limits:**
- Anonymous: 10 req/min
- Authenticated: 100 req/min
- Admin: 1000 req/min

**Acceptance Criteria:**
- [ ] Implement rate limiting middleware (Redis-based)
- [ ] Return 429 Too Many Requests when limit exceeded
- [ ] Include retry-after header
- [ ] Exempt health check endpoints
- [ ] Dashboard to monitor rate limit hits

**Technical Tasks:**
- [ ] Install `slowapi` or implement custom rate limiter
- [ ] Configure Redis key format: `rate_limit:{user_id}:{endpoint}`
- [ ] Add rate limit decorator to API routes
- [ ] Write rate limit tests (simulate burst traffic)
- [ ] Document limits in API docs

**Estimate:** 2 days  
**Dependencies:** 1.1 (Authentication)  

---

#### 2.3 Input Validation & Sanitization
**As a** security engineer  
**I want to** validate all user inputs  
**So that** injection attacks are prevented

**Scope:**
- SQL injection (use parameterized queries only)
- XSS prevention (sanitize HTML inputs)
- Path traversal (validate file paths)
- Command injection (avoid shell commands)

**Acceptance Criteria:**
- [ ] All Pydantic models have strict validation
- [ ] Email format validation (regex)
- [ ] String length limits enforced
- [ ] No raw SQL queries (SQLAlchemy ORM only)
- [ ] File upload validation (if applicable)

**Technical Tasks:**
- [ ] Audit all Pydantic models for validation gaps
- [ ] Add custom validators for complex rules
- [ ] Create input sanitization utility functions
- [ ] Write input validation tests (fuzzing, edge cases)
- [ ] Document validation rules in API docs

**Estimate:** 2 days  
**Dependencies:** None  

---

#### 2.4 Audit Logging Enforcement
**As a** compliance officer  
**I want to** track all sensitive operations  
**So that** we can audit user actions

**Events to Log:**
- User login/logout
- Password changes
- Data access (student records, exam results)
- Data modifications (create/update/delete)
- Permission changes

**Acceptance Criteria:**
- [ ] Audit log table populated automatically
- [ ] Log entries include:
  - Timestamp, user_id, action, resource_type, resource_id
  - IP address, user agent
  - Before/after values (for updates)
- [ ] Admin dashboard to view audit logs
- [ ] Retention policy (90 days)

**Technical Tasks:**
- [ ] Create audit logging middleware
- [ ] Integrate with SQLAlchemy events (after_insert, after_update, after_delete)
- [ ] Add `@audit_log` decorator for manual logging
- [ ] Write audit log viewer API
- [ ] Implement log rotation/archival

**Estimate:** 3 days  
**Dependencies:** None  

---

### Epic 2 Summary
**Total Estimate:** 10 days  
**Target Completion:** Week 6  
**Blockers:** Requires Epic 1 (Authentication) complete  

---

## Epic 3: Advanced CAT Features (Weeks 3-4)

**Priority:** 🟡 Medium  
**Goal:** Enhance adaptive testing with production-grade features

### User Stories

#### 3.1 Exposure Control
**As a** test administrator  
**I want to** limit item reuse  
**So that** exam security is maintained

**Requirements:**
- Track item exposure count per pool
- Limit max exposures (configurable, default: 100)
- Prefer less-exposed items when information is similar

**Acceptance Criteria:**
- [ ] `item_exposure` table to track usage
  - Columns: item_id, pool_id, exposure_count, last_used_at
- [ ] Item selection algorithm considers exposure
  - Filter items with exposure_count < max_exposure
  - Apply penalty to frequently used items
- [ ] Admin dashboard shows exposure statistics
- [ ] Configurable exposure limits per pool

**Technical Tasks:**
- [ ] Create `item_exposure` table (Alembic migration)
- [ ] Update item selection logic in `item_bank.py`
- [ ] Increment exposure count after item use
- [ ] Add exposure control settings (`CAT_MAX_EXPOSURE`)
- [ ] Write exposure control tests

**Estimate:** 3 days  
**Dependencies:** None  

---

#### 3.2 Content Balancing
**As a** test administrator  
**I want to** enforce content distribution  
**So that** exams cover all required topics

**Requirements:**
- Define content blueprints (% per topic/subtopic)
- Select items to match blueprint
- Gracefully degrade if blueprint can't be met

**Example Blueprint:**
```json
{
  "algebra": 40,
  "geometry": 30,
  "statistics": 30
}
```

**Acceptance Criteria:**
- [ ] Blueprint table to store content requirements
  - Columns: pool_id, topic, target_percentage
- [ ] Item selection respects blueprint
  - Track current distribution during exam
  - Adjust selection probabilities to meet targets
- [ ] Deviation tolerance (±5%)
- [ ] Admin UI to define blueprints

**Technical Tasks:**
- [ ] Create `content_blueprint` table (Alembic migration)
- [ ] Implement content balancing algorithm
- [ ] Add blueprint enforcement to item selection
- [ ] Create blueprint management API
- [ ] Write content balancing tests

**Estimate:** 4 days  
**Dependencies:** None  

---

#### 3.3 Multi-Stage Adaptive Testing (Optional)
**As a** test administrator  
**I want to** use multi-stage routing  
**So that** exams are more efficient

**Stages:**
1. **Routing Stage:** 5-7 items, classify ability level (low/medium/high)
2. **Measurement Stage:** 10-15 items, precise estimation within level
3. **Verification Stage:** 3-5 items, confirm final score

**Acceptance Criteria:**
- [ ] Define stage configurations
- [ ] Implement stage transitions
- [ ] Adjust item pools per stage
- [ ] Track stage-specific metrics

**Technical Tasks:**
- [ ] Create `exam_stage` enum
- [ ] Update `exam_sessions` table with stage tracking
- [ ] Modify item selection to respect stages
- [ ] Write multi-stage tests

**Estimate:** 5 days  
**Dependencies:** 3.1, 3.2  
**Priority:** Low (defer if time constrained)  

---

### Epic 3 Summary
**Total Estimate:** 7-12 days  
**Target Completion:** Week 4  
**Blockers:** None (can be parallelized with Epic 1)  

---

## Epic 4: E2E Testing & CI/CD (Continuous)

**Priority:** 🟢 Medium  
**Goal:** Achieve reliable automated testing

### User Stories

#### 4.1 E2E Test Stabilization
**As a** developer  
**I want** E2E tests to run reliably  
**So that** I can trust CI/CD results

**Root Cause Analysis:**
- [ ] Identify why `test_adaptive_exam_complete_flow` hangs
- [ ] Possible causes:
  - DB connection pool exhaustion
  - Redis timeout configuration
  - Infinite loop in CAT engine
  - Test environment mismatch

**Acceptance Criteria:**
- [ ] All E2E tests pass consistently (0% flakiness)
- [ ] Test execution time < 10 seconds
- [ ] Tests run in isolated containers
- [ ] Clear error messages on failure

**Technical Tasks:**
- [ ] Add extensive logging to E2E tests
- [ ] Set aggressive timeouts (5s per test)
- [ ] Run tests in Docker Compose environment
- [ ] Add database/Redis cleanup between tests
- [ ] Re-enable skipped tests one by one

**Estimate:** 3 days  
**Dependencies:** None  
**Priority:** High (blocking CI/CD confidence)  

---

#### 4.2 CI/CD Pipeline
**As a** team member  
**I want** automated testing on every commit  
**So that** bugs are caught early

**Pipeline Stages:**
1. Lint (ruff, black, mypy)
2. Unit tests (pytest)
3. Integration tests (pytest with Docker Compose)
4. Security scan (bandit, safety)
5. Build Docker images
6. Deploy to staging (if main branch)

**Acceptance Criteria:**
- [ ] GitHub Actions workflow configured
- [ ] All tests run on pull requests
- [ ] Branch protection requires passing tests
- [ ] Test results visible in PR comments
- [ ] Deployment to staging on merge

**Technical Tasks:**
- [ ] Create `.github/workflows/ci.yml`
- [ ] Set up test database in CI (Docker)
- [ ] Configure secrets (DB password, API keys)
- [ ] Add status badges to README
- [ ] Document CI/CD process

**Estimate:** 2 days  
**Dependencies:** 4.1 (E2E Stability)  

---

### Epic 4 Summary
**Total Estimate:** 5 days  
**Target Completion:** Ongoing (Week 1, 3, 6)  
**Blockers:** Requires Docker Compose stability  

---

## Epic 5: Monitoring & Observability (Weeks 7-8)

**Priority:** 🟡 Medium  
**Goal:** Gain visibility into system health and performance

### User Stories

#### 5.1 Prometheus Metrics
**As an** operations engineer  
**I want to** collect system metrics  
**So that** I can detect issues proactively

**Metrics to Track:**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Database query time
- Redis operation time
- Active exam sessions
- Item selection time

**Acceptance Criteria:**
- [ ] Prometheus client library integrated
- [ ] `/metrics` endpoint exposed
- [ ] Custom metrics for CAT operations
- [ ] Scrape interval: 15 seconds
- [ ] Retention: 30 days

**Technical Tasks:**
- [ ] Install `prometheus-fastapi-instrumentator`
- [ ] Add custom metrics for CAT engine
- [ ] Create `docker-compose.monitoring.yml` (Prometheus + Grafana)
- [ ] Configure Prometheus scrape targets
- [ ] Write metrics export tests

**Estimate:** 2 days  
**Dependencies:** None  

---

#### 5.2 Grafana Dashboards
**As an** operations engineer  
**I want to** visualize metrics  
**So that** I can understand system behavior

**Dashboards:**
1. **System Overview:** CPU, memory, disk, network
2. **API Performance:** Request rate, response time, error rate
3. **CAT Engine:** Exam sessions, θ convergence, item selection time
4. **Database:** Query rate, slow queries, connection pool

**Acceptance Criteria:**
- [ ] Grafana accessible at `http://localhost:3000`
- [ ] 4 pre-configured dashboards
- [ ] Alerts for critical thresholds
- [ ] Export dashboard JSON for version control

**Technical Tasks:**
- [ ] Set up Grafana container
- [ ] Configure Prometheus data source
- [ ] Create dashboard JSON files
- [ ] Add alerting rules
- [ ] Document dashboard setup

**Estimate:** 2 days  
**Dependencies:** 5.1 (Prometheus)  

---

#### 5.3 Structured Logging
**As a** developer  
**I want** structured JSON logs  
**So that** I can query logs efficiently

**Log Format:**
```json
{
  "timestamp": "2025-11-24T10:30:00Z",
  "level": "INFO",
  "logger": "adaptive_exam",
  "message": "Exam session started",
  "context": {
    "session_id": 123,
    "student_id": 456,
    "initial_theta": 0.0
  }
}
```

**Acceptance Criteria:**
- [ ] All logs in JSON format
- [ ] Correlation ID across requests
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [ ] Sensitive data redacted (passwords, tokens)

**Technical Tasks:**
- [ ] Install `python-json-logger`
- [ ] Configure logging in `backend/app/core/logging.py`
- [ ] Add correlation ID middleware
- [ ] Update all log statements
- [ ] Write logging tests

**Estimate:** 2 days  
**Dependencies:** None  

---

#### 5.4 Error Tracking (Sentry)
**As a** developer  
**I want** to be notified of errors  
**So that** I can fix bugs quickly

**Features:**
- Exception capture
- Stack traces
- User context
- Breadcrumbs (recent actions)
- Release tracking

**Acceptance Criteria:**
- [ ] Sentry SDK integrated
- [ ] Errors sent to Sentry dashboard
- [ ] User ID attached to errors
- [ ] Environment tags (dev, staging, prod)
- [ ] Email alerts for critical errors

**Technical Tasks:**
- [ ] Create Sentry account/project
- [ ] Install `sentry-sdk[fastapi]`
- [ ] Configure Sentry DSN (environment variable)
- [ ] Add custom error context
- [ ] Write error tracking tests

**Estimate:** 1 day  
**Dependencies:** None  

---

### Epic 5 Summary
**Total Estimate:** 7 days  
**Target Completion:** Week 8  
**Blockers:** None (nice-to-have for MVP)  

---

## Backlog Summary

| Epic | Priority | Estimate | Weeks | Dependencies |
|------|----------|----------|-------|--------------|
| 1. Authentication & Authorization | 🔴 Critical | 8-10 days | 1-2 | None |
| 2. Security Hardening | 🟠 High | 10 days | 5-6 | Epic 1 |
| 3. Advanced CAT Features | 🟡 Medium | 7-12 days | 3-4 | None |
| 4. E2E Testing & CI/CD | 🟢 Medium | 5 days | Ongoing | None |
| 5. Monitoring & Observability | 🟡 Medium | 7 days | 7-8 | None |
| **Total** | | **37-44 days** | **8 weeks** | |

---

## Phase 1.0 Roadmap

### Week 1-2: Authentication (🔴 Critical)
- User registration, login, JWT
- Role-based access control
- Password reset flow

### Week 3-4: Advanced CAT (🟡 Medium)
- Exposure control
- Content balancing
- Multi-stage testing (optional)

### Week 5-6: Security Hardening (🟠 High)
- PostgreSQL RLS policies
- API rate limiting
- Input validation
- Audit logging

### Week 7-8: Monitoring & Polish (🟡 Medium)
- Prometheus + Grafana
- Structured logging
- Error tracking
- Final E2E tests

---

## Definition of Done (Phase 1.0)

**Must Have:**
- ✅ All users authenticate with JWT
- ✅ RBAC enforced on all endpoints
- ✅ PostgreSQL RLS policies active
- ✅ API rate limiting in place
- ✅ E2E tests pass consistently
- ✅ Monitoring dashboards operational

**Nice to Have:**
- OAuth2 integration
- Multi-stage adaptive testing
- Comprehensive API documentation
- Load testing results (100+ concurrent users)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Authentication delays Phase 1.0 | High | Use FastAPI-Users library (battle-tested) |
| RLS policies break existing queries | Medium | Thorough testing in dev environment first |
| E2E tests remain unstable | Medium | Allocate dedicated time; seek external review if needed |
| Scope creep | High | Strict prioritization; defer non-critical features |

---

## Next Steps

1. **Review this backlog** with the team
2. **Break down Epic 1** into detailed tasks (Jira/GitHub Issues)
3. **Set up development environment** for Phase 1.0
4. **Begin Epic 1: User Registration** (target: November 25, 2025)

---

**Phase 1.0 Status:** 📋 **READY TO START**  
**Target Launch:** January 20, 2026 (8 weeks from now)  
**Approval:** Pending team review  

---

**End of Phase 1.0 Initial Backlog**
