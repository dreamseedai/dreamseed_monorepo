# Week 4: Deployment & E2E Testing Tasks

**Period:** December 16-22, 2025  
**Goal:** Production deployment + Beta testing  
**Status:** 📋 Not Started  
**Current Date:** November 26, 2025

---

## 📋 Week 4 Overview

**Primary Goals:**
1. ✅ Fix performance bottleneck (`/api/auth/register` slow)
2. 🚀 Docker Compose deployment setup
3. 🧪 E2E testing automation
4. 🌐 Production server configuration
5. 👥 Beta tester onboarding (5-10 users)

**Success Criteria:**
- [ ] Register endpoint < 1 second
- [ ] Docker Compose fully functional
- [ ] E2E tests pass
- [ ] SSL certificate configured
- [ ] 5+ beta testers complete full flow

---

## 🔥 Priority 1: Performance Optimization (CURRENT)

### Issue: `/api/auth/register` 느린 응답

**Diagnosis (Nov 26):**
- ✅ Windsurf test: `HTTP 404`, `0.55ms` - 서버 자체는 정상
- ✅ VS Code test: Tool call execution blocked/cancelled
- ⚠️ `/api/auth/register` endpoint 404 - routing issue suspected
- ✅ `/docs` endpoint: `0.008s` - uvicorn healthy

**Root Cause Analysis:**
- Server infrastructure: ✅ Healthy
- Network: ✅ Healthy (localhost)
- Bottleneck: UserManager hooks (email sending)

**Solution Implemented:**
1. ✅ `EMAIL_MODE=console` for dev (skip SMTP)
2. ✅ `email_service.py` created (console/smtp mode)
3. ✅ UserManager hooks updated with timing logs
4. ✅ `.env` updated with `EMAIL_MODE=console`

**Files Modified:**
```
backend/app/core/users.py                  ✅ Timing logs + EMAIL_MODE
backend/app/services/email_service.py      ✅ Created (console/smtp)
backend/app/api/routers/auth.py           ✅ Diagnostic endpoint
backend/.env                              ✅ EMAIL_MODE=console
```

**Deployment Attempt (Nov 27, 2025):**
1. ✅ Created new release: `/opt/dreamseed/releases/2025-11-27_0157`
2. ✅ Copied new code with rsync
3. ❌ Dependency mismatch: Old .venv missing `psycopg` module
4. ❌ Import errors: SQLAlchemy table duplication issues
5. 🔄 Rolled back to: `/opt/dreamseed/releases/2025-09-15_2048`

**Blockers Identified:**
- Development code uses different dependencies than production .venv
- `app.main` import path issues in new code structure
- SQLAlchemy MetaData conflicts (organizations table) - **PARTIALLY FIXED**
- SQLAlchemy relationship conflicts: Multiple "Organization" classes in registry
- nest_asyncio vs uvloop conflict - **FIXED**

**Next Steps:**
1. 🔧 Fix development environment import errors
2. 🔧 Resolve SQLAlchemy table duplication
3. ✅ Create proper .venv for new release
4. ⏸️ Test with port 8001 (isolated environment)
5. ⏸️ Measure performance improvement
6. ⏸️ Document Before/After comparison

---

## 🐳 Task Group 1: Docker Compose Setup

### 1.1 Create docker-compose.phase1.yml ✅

**File:** `/home/won/projects/dreamseed_monorepo/docker-compose.phase1.yml`

**Status:** ✅ Already exists (from Phase 0)

**Services:**
- PostgreSQL 15 (port 5432)
- Redis 7 (port 6379)
- Backend (FastAPI, port 8000)
- Student Frontend (Next.js, port 3001)
- Nginx reverse proxy (port 80/443)

**Verification:**
```bash
cd /home/won/projects/dreamseed_monorepo
docker compose -f docker-compose.phase1.yml ps
```

**Expected Output:**
```
NAME                STATUS    PORTS
postgres            Up        5432
redis               Up        6379
backend             Up        8000
student-front       Up        3001
nginx               Up        80,443
```

---

### 1.2 Create Dockerfile for Student Frontend

**File:** `apps/student_front/Dockerfile`

**Status:** ✅ Already exists

**Contents:**
```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3001
CMD ["node", "server.js"]
```

---

### 1.3 Update Backend Dockerfile

**File:** `backend/Dockerfile`

**Status:** ✅ Already exists

**Ensure includes:**
- Python 3.11+
- FastAPI dependencies
- WeasyPrint (for PDF generation)
- Korean fonts

---

### 1.4 Environment Configuration

**File:** `.env.phase1.example`

**Status:** ✅ Already exists

**Create production `.env`:**
```bash
cp .env.phase1.example .env.phase1
# Edit with production values:
# - Database password
# - JWT_SECRET (secure random)
# - SMTP credentials (if EMAIL_MODE=smtp)
```

---

## 🧪 Task Group 2: E2E Testing

### 2.1 Create E2E Test Script

**File:** `scripts/e2e_test_phase1.sh`

**Status:** ✅ Already exists

**Test Scenarios:**
1. Health check (backend /health)
2. Register new user
3. Login with credentials
4. Access /me endpoint with token
5. Frontend homepage accessible

**Usage:**
```bash
cd /home/won/projects/dreamseed_monorepo
chmod +x scripts/e2e_test_phase1.sh
./scripts/e2e_test_phase1.sh
```

---

### 2.2 Verify All Services Running

**Script:** Automated health checks

```bash
#!/bin/bash
echo "=== Week 4 Service Health Check ==="

# 1. Backend
curl -f http://localhost:8000/health || echo "❌ Backend down"

# 2. Student Frontend
curl -f http://localhost:3001 || echo "❌ Frontend down"

# 3. PostgreSQL
pg_isready -h localhost -p 5432 || echo "❌ PostgreSQL down"

# 4. Redis
redis-cli -p 6379 ping || echo "❌ Redis down"

echo "✅ All services healthy"
```

---

### 2.3 Run Full E2E Flow

**Manual Test Checklist:**
- [ ] Navigate to http://localhost:3001
- [ ] Click "Register"
- [ ] Fill form: test_e2e@dreamseed.ai / TestPass123!
- [ ] Submit → Should redirect to /dashboard
- [ ] Check localStorage for access_token
- [ ] Navigate to /exams
- [ ] Click "Start Exam" (if exam available)
- [ ] Complete at least 1 question
- [ ] Check /results page

---

## 🌐 Task Group 3: Production Deployment

### 3.1 Server Provisioning

**Options:**
- **Option A:** Use existing server (192.168.68.116)
- **Option B:** Provision new GCP/AWS instance

**Requirements:**
- Ubuntu 22.04+
- Docker & Docker Compose installed
- Ports 80/443 open
- 2GB+ RAM, 20GB+ disk

**Verification:**
```bash
ssh user@server
docker --version
docker compose version
```

---

### 3.2 DNS Configuration

**Domain:** dreamseedai.com

**DNS Records (Cloudflare):**
```
Type   Name    Content              TTL
A      @       <server-ip>          Auto
A      www     <server-ip>          Auto
CNAME  api     dreamseedai.com      Auto
```

---

### 3.3 SSL Certificate Setup

**Option A: Caddy (Recommended)**
```bash
# Install Caddy
sudo apt install -y caddy

# Caddyfile
dreamseedai.com {
    reverse_proxy localhost:3001
}

api.dreamseedai.com {
    reverse_proxy localhost:8000
}

# Start Caddy
sudo systemctl start caddy
```

**Option B: Let's Encrypt + Nginx**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dreamseedai.com -d www.dreamseedai.com
```

---

### 3.4 Deploy Application

**Steps:**
```bash
# 1. Clone repository
git clone https://github.com/dreamseedai/dreamseed_monorepo.git
cd dreamseed_monorepo

# 2. Create .env.phase1
cp .env.phase1.example .env.phase1
nano .env.phase1  # Edit production values

# 3. Build and start
docker compose -f docker-compose.phase1.yml up -d --build

# 4. Verify
docker compose -f docker-compose.phase1.yml ps
docker compose -f docker-compose.phase1.yml logs -f backend

# 5. Run migrations
docker compose -f docker-compose.phase1.yml exec backend alembic upgrade head

# 6. Seed data (if needed)
docker compose -f docker-compose.phase1.yml exec backend python scripts/seed_data.py
```

---

## 👥 Task Group 4: Beta Testing

### 4.1 Create Beta Tester Guide

**File:** `docs/beta/BETA_TESTER_GUIDE.md`

**Contents:**
- Welcome message
- Login instructions
- Test scenarios
- Feedback form link
- Known issues

---

### 4.2 Recruit 5-10 Beta Testers

**Target Audience:**
- 2-3 students (middle/high school)
- 1-2 teachers
- 1-2 parents
- 1 developer friend

**Onboarding:**
1. Send invite email with guide
2. Create test accounts
3. Share credentials securely
4. Schedule 1-hour test session

---

### 4.3 Feedback Collection

**Google Form Questions:**
1. Registration smooth? (1-5)
2. Login smooth? (1-5)
3. Dashboard clear? (1-5)
4. Exam flow smooth? (1-5)
5. Results page helpful? (1-5)
6. What was confusing?
7. What feature would you add?
8. Would you use this? (Yes/No/Maybe)

**Link:** https://forms.google.com/...

---

## 📊 Week 4 Checklist

### Performance (Current Priority)
- [x] EMAIL_MODE=console implemented ✅
- [x] email_service.py created ✅
- [x] UserManager hooks optimized ✅
- [x] Attempted production deployment ⚠️ (blocked by dependencies)
- [ ] 🔧 Fix import errors (SQLAlchemy, app.main)
- [ ] 🔧 Fix development environment
- [ ] Verify register endpoint works
- [ ] Measure actual performance improvement
- [ ] Document before/after metrics

### Docker
- [x] docker-compose.phase1.yml exists ✅
- [x] Student Frontend Dockerfile exists ✅
- [x] Backend Dockerfile exists ✅
- [ ] Test full stack with `docker compose up`
- [ ] Verify all health checks pass

### E2E Testing
- [x] e2e_test_phase1.sh exists ✅
- [ ] Run E2E test script
- [ ] Fix any failing tests
- [ ] Document test results

### Deployment
- [ ] Provision production server
- [ ] Configure DNS (dreamseedai.com)
- [ ] Setup SSL certificate
- [ ] Deploy with Docker Compose
- [ ] Verify production health

### Beta Testing
- [ ] Create beta tester guide
- [ ] Recruit 5-10 testers
- [ ] Onboard testers
- [ ] Collect feedback
- [ ] Document findings

---

## 🐛 Known Issues

### Issue 1: Register Endpoint 404
**Status:** 🔴 Blocker  
**Description:** `/api/auth/register` returns 404  
**Possible Causes:**
- Server not restarted after code changes
- Router not included in main.py
- CORS configuration issue

**Debug Steps:**
```bash
# 1. Check if server loaded new code
curl http://localhost:8000/api/auth/register_dev
# Should return 200 if new routes loaded

# 2. Check FastAPI routes
curl http://localhost:8000/docs
# Look for /api/auth/register in Swagger UI

# 3. Check server logs
tail -f /path/to/uvicorn.log
```

### Issue 2: VS Code Tool Execution
**Status:** 🟡 Known Limitation  
**Description:** GitHub Copilot tool calls frequently cancelled  
**Workaround:** Use Windsurf for terminal commands

---

## 📈 Success Metrics

### Technical
- [ ] Register endpoint < 1s (Current: TBD)
- [ ] E2E tests pass (Current: Not run)
- [ ] Docker Compose starts (Current: Not tested)
- [ ] SSL certificate valid (Current: Not configured)
- [ ] Uptime > 95% (7 days)

### User Experience
- [ ] 5+ beta testers registered
- [ ] 20+ exams completed
- [ ] Average satisfaction > 3.5/5
- [ ] 0 critical bugs reported
- [ ] 3+ positive feedback items

---

## 🎯 Week 4 Timeline

### Day 1 (Dec 16): Performance & Docker
- AM: Fix register endpoint issue
- PM: Test Docker Compose full stack

### Day 2 (Dec 17): E2E Testing
- AM: Run and fix E2E tests
- PM: Document test results

### Day 3 (Dec 18): Deployment Prep
- AM: Server provisioning
- PM: DNS + SSL configuration

### Day 4 (Dec 19): Production Deploy
- AM: Deploy to production
- PM: Smoke test production

### Day 5 (Dec 20): Beta Testing
- AM: Onboard beta testers
- PM: Monitor and support

### Day 6-7 (Dec 21-22): Feedback & Fixes
- Collect feedback
- Fix critical bugs
- 🎉 **Alpha Launch!**

---

## 📚 Related Documents

- [PHASE1_STATUS.md](./PHASE1_STATUS.md) - Overall Phase 1 progress
- [WEEK4_ALPHA_TEST_RUNBOOK.md](./WEEK4_ALPHA_TEST_RUNBOOK.md) - Detailed test scenarios
- [PHASE1_ALPHA_CHECKLIST.md](./PHASE1_ALPHA_CHECKLIST.md) - Acceptance criteria

---

## ✅ Completion Criteria

Week 4 is complete when:
1. ✅ Register endpoint < 1 second
2. ✅ Docker Compose working
3. ✅ E2E tests pass
4. ✅ Production deployed (dreamseedai.com)
5. ✅ SSL configured
6. ✅ 5+ beta testers onboarded
7. ✅ Feedback collected
8. ✅ 0 critical bugs

**Target:** December 22, 2025  
**Status:** 📋 Week 4 Day 0 (Nov 26)

---

**Last Updated:** November 26, 2025  
**Next Review:** December 16, 2025 (Week 4 start)
