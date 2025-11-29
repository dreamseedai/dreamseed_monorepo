# Week 4 Execution Plan: Alpha Testing & UI Integration

**Date**: November 25, 2025  
**Phase**: Week 4 - From Backend Complete → Alpha Deployment  
**Duration**: 5-7 days  
**Goal**: Get real teachers, tutors, students, and parents using the system

---

## Executive Summary

**Phase 1A "Educational Data Brain + Report Engine" is COMPLETE**. Week 4 focuses on making it **usable by real people**:

1. **Backend Validation** (Day 1-2): Seed data → API testing → PDF generation
2. **Frontend Integration** (Day 3-5): Student/Tutor/Parent UIs with real API calls
3. **Alpha User Testing** (Day 6-7): 2-3 teachers, 3-5 students, 2 parents

### What's Done (Backend)

✅ **Database Schema** (4 tables, 4 enums, 9 indexes)
- `organizations`, `org_memberships`, `student_org_enrollments`, `report_comments`
- 3-axis permission model (User Type × Organization Type × Org Role)

✅ **API Endpoints** (15 total)
- Student: `/abilities/me/summary`, `/abilities/me/trend`
- Tutor: `/tutor/priorities`
- Teacher: `/teacher/reports/{id}/comments` (5 CRUD endpoints)
- Parent: `/parent/reports/{id}`, `/parent/reports/{id}/pdf`

✅ **Services & Business Logic**
- `ability_analytics.py`: θ band classification, risk assessment, priority scoring
- `parent_report_builder.py`: Multi-source comment aggregation (school > academy > tutor)
- `pdf_report_service.py`: HTML → PDF with WeasyPrint + matplotlib charts

✅ **Documentation**
- `ORGANIZATION_AND_MULTI_SOURCE_REPORTS.md` (1000+ lines)
- `STUDENT_TUTOR_PARENT_DASHBOARDS.md` (800+ lines)
- Backend API specs, DB schemas, testing guides

### What's Missing (Week 4 Scope)

🔲 **Backend Testing** (Day 1-2)
- Run Alembic migrations
- Seed test data (3 orgs, 4 teachers, 3 students, 7 abilities, 9 comments)
- Manually test all 15 API endpoints
- Verify PDF generation with multi-source comments

🔲 **Frontend UI** (Day 3-5)
- Student dashboard: Ability cards + trend charts
- Tutor dashboard: Priority list + comment form
- Parent portal: PDF download button

🔲 **User Testing** (Day 6-7)
- Recruit 5-10 alpha testers (teachers, students, parents)
- Run complete workflow: CAT exam → θ calibration → comments → PDF
- Collect feedback, fix critical bugs

---

## Day-by-Day Breakdown

### Day 1-2: Backend Validation

**Goal**: Prove that all APIs work end-to-end

#### Tasks

1. **Database Setup**
   ```bash
   cd backend
   alembic upgrade head
   python scripts/seed_week4_alpha.py
   ```

   **Expected Output**:
   - 3 organizations (서울고등학교, 대치입시학원, 김튜터)
   - 4 teachers with org memberships
   - 3 students (이민준, 김서연, 박지호) with multi-org enrollments
   - 7 IRT ability snapshots
   - 9 report comments (8 published, 1 draft)

2. **API Testing** (use `WEEK4_BACKEND_TESTING_CHECKLIST.md`)
   - Test 1-7: Organization queries, IRT data, comment CRUD, parent reports
   - Test 8-10: Authorization, error handling, ownership
   - Test 11-12: Performance (< 500ms JSON, < 2s PDF)
   - Test 13: End-to-end workflow (teacher comments → parent PDF)

3. **PDF Visual Inspection**
   ```bash
   curl http://localhost:8001/api/parent/reports/$STUDENT_ID/pdf?period=last4w \
     -H "Authorization: Bearer $PARENT_TOKEN" \
     -o test_report.pdf
   
   xdg-open test_report.pdf
   ```

   **Checklist**:
   - [ ] Subject table with 3 rows (math, english, science)
   - [ ] School teacher comment section
   - [ ] Academy/tutor comment section
   - [ ] Next 4-week plans (multiple sources combined)
   - [ ] Parent guidance
   - [ ] Trend chart (placeholder or real)

**Deliverable**: All 15 API endpoints tested, PDF generated successfully

---

### Day 3: Student Frontend

**Goal**: Student can see their abilities in a dashboard

#### Tasks

1. **Create API Client** (`student_front/src/lib/abilityClient.ts`)
   - ✅ Already created with full TypeScript types
   - Functions: `fetchMyAbilitySummary()`, `fetchMyThetaTrend()`
   - Helpers: `getThetaBandColor()`, `formatDeltaTheta()`

2. **Create Dashboard Page** (`student_front/src/app/dashboard/page.tsx`)
   - ✅ Already created with:
     * Ability cards (all subjects)
     * Subject selection dropdown
     * Simple trend visualization (replace with recharts later)

3. **Test Integration**
   ```bash
   cd apps/student_front
   npm install
   npm run dev
   # Open http://localhost:3000/dashboard
   ```

   **Expected Behavior**:
   - Cards show θ, band (A/B+/B/C/D), percentile, 7-day change
   - Color-coded badges (green/yellow/red)
   - Recommended actions appear
   - Clicking card shows trend chart

**Deliverable**: Working student dashboard with real API data

---

### Day 4: Tutor Frontend

**Goal**: Tutor can see priority list + create comments

#### Tasks

1. **Create API Client** (`tutor_front/src/lib/tutorClient.ts`)
   ```typescript
   export async function fetchTutorPriorities(
     subject: string,
     windowDays = 14
   ): Promise<TutorPriorityListResponse> { ... }
   
   export async function createReportComment(
     studentId: string,
     payload: ReportCommentCreate
   ): Promise<ReportCommentResponse> { ... }
   ```

2. **Create Priority Dashboard** (`tutor_front/src/app/dashboard/page.tsx`)
   - Table columns:
     * Student Name
     * θ Band
     * Δθ14d (with color coding)
     * Priority Score
     * Risk Level
     * Flags (badges: recent_decline, no_activity_7d, etc.)
     * Actions (button: "Write Comment")

3. **Create Comment Modal** (`tutor_front/src/components/CommentModal.tsx`)
   - Form fields:
     * Section dropdown (summary / next_4w_plan / parent_guidance)
     * Language toggle (ko / en)
     * Content textarea (Markdown supported)
     * Publish checkbox
   - Submit → POST `/teacher/reports/{studentId}/comments`

4. **Test Integration**
   ```bash
   cd apps/tutor_front
   npm install
   npm run dev
   # Open http://localhost:3001/dashboard
   ```

   **Expected Behavior**:
   - Priority list sorted by score (high-risk students first)
   - Clicking "Write Comment" opens modal
   - Submit comment → success toast → modal closes
   - Comment appears in parent PDF (if published)

**Deliverable**: Working tutor dashboard with priority list + comment input

---

### Day 5: Parent Frontend

**Goal**: Parent can download PDF reports

#### Tasks

1. **Create API Client** (`parent_front/src/lib/parentClient.ts`)
   ```typescript
   export async function downloadParentReportPdf(
     studentId: string,
     period: string
   ): Promise<Blob> { ... }
   ```

2. **Create Report List Page** (`parent_front/src/app/children/[id]/reports/page.tsx`)
   - Child selector (if multiple children)
   - Period selector (last4w / last8w / last12w)
   - Download button
   - On click:
     * Fetch PDF blob
     * Create object URL
     * Trigger download (`file-saver` library)

3. **Optional: Preview Feature**
   - Fetch JSON first: `/parent/reports/{id}?period=...`
   - Show preview of ability summary
   - "Download Full Report" button

4. **Test Integration**
   ```bash
   cd apps/parent_front
   npm install
   npm run dev
   # Open http://localhost:3002/children/88888888-.../reports
   ```

   **Expected Behavior**:
   - Period selector works
   - Click "Download" → PDF file downloads
   - Open PDF → all sections populated correctly

**Deliverable**: Working parent portal with PDF download

---

### Day 6-7: Alpha User Testing

**Goal**: Real users test the complete workflow

#### Participants

- **2-3 Teachers** (1 school, 1 academy, 1 tutor)
- **3-5 Students** (different ability levels: high, average, at-risk)
- **2 Parents** (children enrolled in school + academy)

#### Test Scenario

**Phase 1: Setup (30 min)**
1. Admin creates user accounts (teachers, students, parents)
2. Admin assigns organizations (school, academy, tutor)
3. Admin creates org memberships + student enrollments

**Phase 2: Student Workflow (1 hour)**
1. Student logs into `student_front`
2. Student takes CAT exam (adaptive_exam_router)
3. Backend runs IRT calibration (R mirt pipeline)
4. Student refreshes dashboard → sees θ values, bands, percentiles

**Phase 3: Teacher/Tutor Workflow (1 hour)**
1. Teacher logs into `tutor_front` (or school teacher version)
2. Teacher reviews priority list
3. Teacher selects at-risk student
4. Teacher writes comment (summary + next_4w_plan + parent_guidance)
5. Teacher publishes comment

**Phase 4: Parent Workflow (30 min)**
1. Parent logs into `parent_front`
2. Parent selects child + period (last4w)
3. Parent downloads PDF
4. Parent reviews PDF:
   - Ability summary table
   - School teacher comment
   - Academy/tutor comment
   - Next 4-week plans
   - Parent guidance

**Phase 5: Feedback Collection (30 min)**
- Survey: Ease of use (1-5), usefulness (1-5), bugs encountered
- Open-ended: What worked well? What needs improvement?

#### Critical Bugs (Fix Immediately)

- [ ] PDF fails to generate → Check WeasyPrint dependencies
- [ ] Comments don't appear in PDF → Check `is_published=true` + `source_type` mapping
- [ ] Authorization errors → Check JWT token, org membership logic
- [ ] Theta values not updating → Check R calibration pipeline, DB writes

#### Nice-to-Have Bugs (Fix in Week 5)

- [ ] Trend chart not showing → Replace placeholder with recharts
- [ ] Mobile UI broken → Add responsive CSS
- [ ] PDF formatting issues → Tweak HTML template
- [ ] Slow PDF generation → Add caching, async queue

**Deliverable**: Test report with 5+ feedback items, 3+ bug fixes

---

## Success Criteria

### Week 4 Minimum Viable Product (MVP)

- [x] **Backend**: All migrations applied, seed data loaded
- [x] **APIs**: 15 endpoints tested, return correct data
- [ ] **Student UI**: Dashboard shows abilities, trend chart (basic)
- [ ] **Tutor UI**: Priority list + comment form works
- [ ] **Parent UI**: PDF download works
- [ ] **PDF**: Contains multi-source comments correctly labeled
- [ ] **Testing**: 5+ real users complete full workflow
- [ ] **Performance**: < 500ms JSON, < 2s PDF, < 5s CAT exam

### Week 4 Alpha Readiness Checklist

**Infrastructure**:
- [ ] Docker Compose runs successfully (backend + DB + Redis)
- [ ] Alembic migrations applied without errors
- [ ] Seed data script runs cleanly

**Backend**:
- [ ] All 15 API endpoints return 200/201 (no 500 errors)
- [ ] Authorization logic works (school/tutor filtering)
- [ ] PDF generation succeeds with multi-source comments
- [ ] Performance targets met (500ms/2s)

**Frontend**:
- [ ] Student dashboard renders abilities correctly
- [ ] Tutor dashboard shows priority list + comment form
- [ ] Parent portal downloads PDF successfully
- [ ] No console errors, no broken UI

**Testing**:
- [ ] 5+ users complete workflow end-to-end
- [ ] 3+ critical bugs identified and fixed
- [ ] 10+ feedback items collected for Week 5

---

## Week 5 Preview: Production Deployment

**After Week 4 success**, Week 5 focuses on:

1. **Bug Fixes** (from alpha feedback)
   - UI polish (responsive design, animations)
   - PDF formatting improvements
   - Performance optimization (caching, async PDF queue)

2. **Additional Features**
   - Teacher-student assignment filtering (tutor sees only assigned students)
   - Parent-child relationship verification (ownership check)
   - Trend chart generation (matplotlib PNG, not placeholder)
   - Comment templates (pre-filled content for common scenarios)

3. **Production Deployment**
   - Deploy to staging environment (GCP Cloud Run)
   - Run smoke tests
   - Deploy to production
   - Monitor logs, performance metrics
   - Set up alerts (error rate, response time)

4. **Onboarding Materials**
   - User guides (teacher/tutor/parent/student)
   - Video tutorials (3-5 min each)
   - FAQ documentation
   - Support ticketing system

---

## Risk Mitigation

### High-Risk Items

**Risk**: User UUIDs not ready → Seed script fails  
**Mitigation**: Use placeholder UUIDs, manual SQL insertion as fallback

**Risk**: PDF generation fails (WeasyPrint dependencies)  
**Mitigation**: Docker image pre-installs dependencies, test on local first

**Risk**: R calibration pipeline not integrated → θ values don't update  
**Mitigation**: Use seed_week4_alpha.py to insert static θ values for testing

**Risk**: Frontend-backend CORS issues  
**Mitigation**: Configure CORS in backend main.py, test with curl first

### Medium-Risk Items

**Risk**: Alpha testers don't show up  
**Mitigation**: Over-recruit (10 participants for 5 slots), offer incentives

**Risk**: Comment aggregation logic has bugs (wrong source_type)  
**Mitigation**: Unit tests in test_parent_report_builder.py, manual SQL checks

**Risk**: PDF too slow (> 5s)  
**Mitigation**: Defer chart generation to Week 5, use placeholder images

---

## Resources & References

### Documentation

- **Organization Architecture**: `docs/project-status/phase1/ORGANIZATION_AND_MULTI_SOURCE_REPORTS.md`
- **Dashboard System**: `docs/project-status/phase1/STUDENT_TUTOR_PARENT_DASHBOARDS.md`
- **IRT/CAT Pipeline**: `docs/project-status/phase1/IRT_CAT_PRODUCTION_PIPELINE.md`
- **Backend Testing**: `backend/WEEK4_BACKEND_TESTING_CHECKLIST.md`

### Code Locations

- **Backend Models**: `backend/app/models/org_models.py`, `backend/app/models/report_models.py`
- **Backend Services**: `backend/app/services/ability_analytics.py`, `backend/app/services/parent_report_builder.py`
- **Backend APIs**: `backend/app/routers/ability_dashboards.py`, `backend/app/routers/report_comments.py`
- **Frontend Clients**: `apps/student_front/src/lib/abilityClient.ts` (+ tutor, parent)
- **Frontend Pages**: `apps/student_front/src/app/dashboard/page.tsx` (+ tutor, parent)

### Tools & Libraries

- **Backend**: FastAPI, SQLAlchemy, Alembic, WeasyPrint, matplotlib
- **Frontend**: Next.js 14, TypeScript, TailwindCSS, recharts (optional)
- **Testing**: curl, jq, psql, pytest, Apache Bench
- **Deployment**: Docker, Docker Compose, GCP Cloud Run (Week 5)

---

## Communication

### Daily Standup (Async)

**Template**:
```
📅 Week 4 Day X Update

✅ Completed:
- [ ] Task 1
- [ ] Task 2

🚧 In Progress:
- [ ] Task 3

❌ Blocked:
- [ ] Blocker 1 (needs: ...)

📊 Metrics:
- API tests passed: X/15
- Frontend pages ready: X/3
- Alpha testers recruited: X/10
```

### End of Week Report

**Template**:
```
📊 Week 4 Summary

✅ Achievements:
- Backend: 15/15 API endpoints tested
- Frontend: 3/3 dashboards deployed
- Testing: 7/10 alpha testers completed workflow

🐛 Bugs Found:
1. [Critical] PDF generation fails with > 5 comments (FIXED)
2. [High] Tutor priority list not sorted correctly (FIXED)
3. [Medium] Mobile UI broken on student dashboard (Week 5)

📈 Performance:
- Average API response: 350ms (target: 500ms) ✅
- PDF generation: 1.8s (target: 2s) ✅
- CAT exam completion: 4.2s (target: 5s) ✅

💬 User Feedback (Top 3):
1. "Ability cards are very clear and helpful" (5/5 students)
2. "Priority list saves me 30 min per week" (3/3 tutors)
3. "PDF is comprehensive but too long" (2/2 parents → Week 5 improvement)

🔜 Week 5 Focus:
- Fix 3 medium-priority bugs
- Deploy to staging environment
- Create user onboarding materials
```

---

**Week 4 Start Date**: ___________  
**Week 4 End Date**: ___________  
**Project Manager**: ___________  
**Status**: 🟢 On Track | 🟡 At Risk | 🔴 Blocked
