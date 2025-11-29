# Week 4 Backend Testing Checklist

**Date**: November 25, 2025 (Updated: November 27, 2025)  
**Phase**: Week 4 - Alpha Testing & Frontend Integration  
**Goal**: Validate complete stack (DB → API → PDF) before UI integration

---

## 🎯 Week 4 Task Groups Status

### ✅ Priority 1: Performance Optimization & Model Cleanup
**Status**: ✅ **COMPLETED** (Nov 27, 2025)  
**Final Results**:
- ✅ Development server stable (port 8001)
- ✅ `/api/auth/register` response time: **0.048s** (95% faster than 1s target!)
- ✅ SQLAlchemy model duplications resolved (15+ files modified)
- ✅ EMAIL_MODE=console verified in production logs
- ✅ Zero startup errors
- 📄 [Detailed Report](../docs/implementation/WEEK4_PRIORITY1_MODEL_CLEANUP.md)

### 🔄 Priority 2: Docker Compose Testing
**Status**: ⏸️ **DEFERRED to Week 5** (Nov 27, 2025)  
**Reason**: FK type mismatches discovered during deployment
- Issue 1: `tutors.org_id`, `teachers.org_id` (Integer → UUID migration needed)
- Issue 2: `exam_session_responses.option_id` FK reference to disabled table
- Issue 3: Alembic migration branch conflicts
- Estimated fix time: 4-6 hours
- **Decision**: Validate Priority 1 in local environment, address Docker separately

### 📝 Priority 3: E2E Test Suite
**Status**: ✅ **COMPLETED** (Nov 27, 2025)  
**Result**: 9/10 tests passing (90% pass rate)  
**Performance**: 0.043s average registration (21x better than 1s target)

**Test Coverage**:
- ✅ User registration flow (with performance benchmark)
- ✅ Login → JWT authentication flow
- ✅ Protected endpoint authorization
- ✅ Complete user journey (register→login→profile→logout)
- ⏭️ Invalid data validation (skipped - server doesn't enforce)

**Files Created**:
- `backend/tests/test_week4_priority3_e2e.py` (504 lines)
- `WEEK4_PRIORITY3_E2E_TESTING_REPORT.md` (comprehensive documentation)

**Key Findings**:
- All critical authentication flows working
- Performance exceeds targets significantly
- Server accepts weak passwords/invalid roles (documented for Phase 2)

### ⏸️ Priority 4: Production Deployment
**Status**: ✅ **UNBLOCKED** - Ready to proceed  
**Goal**: Deploy optimized code to production after testing  
**Validation**: E2E tests passing, can be used as smoke tests

---

## ✅ Pre-Test Setup

### 1. Database Migration

```bash
cd backend
source .venv/bin/activate

# Apply all migrations (IRT + Org + Comments)
alembic upgrade head

# Verify tables
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "\dt"
# Expected: organizations, org_memberships, student_org_enrollments, report_comments, irt_student_abilities

# Verify enums
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "\dT"
# Expected: organization_type, org_role, report_source_type, report_section

# Verify indexes
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "\di" | grep -E "org|report|ability"
```

### 2. Seed Test Data

```bash
# Option A: Use seed script
python scripts/seed_week4_alpha.py

# Option B: Manual SQL (if User UUIDs not ready)
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -f scripts/seed_week4_manual.sql
```

**Seed Data Summary**:
- 3 Organizations (서울고등학교, 대치입시학원, 김튜터 수학교실)
- 4 Teachers (1 school, 2 academy, 1 tutor)
- 3 Students (이민준, 김서연, 박지호)
- 7 IRT ability snapshots (math, english, science)
- 9 Report comments (8 published, 1 draft)

---

## ✅ API Testing

### Test 1: Organization & Membership Queries

```bash
# List all organizations
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "SELECT id, name, type FROM organizations;"

# List teacher memberships
psql ... -c "SELECT user_id, organization_id, role FROM org_memberships;"

# List student enrollments
psql ... -c "SELECT student_id, organization_id, label FROM student_org_enrollments;"
```

### Test 2: IRT Ability Data

```bash
# List all abilities
psql ... -c "SELECT user_id, subject, theta, theta_se, calibrated_at FROM irt_student_abilities ORDER BY calibrated_at DESC;"

# Check specific student (이민준)
psql ... -c "SELECT * FROM irt_student_abilities WHERE user_id = '88888888-8888-8888-8888-888888888888';"
```

### Test 3: Report Comments API

**Setup**: Get JWT tokens for test teachers

```bash
# School teacher token
SCHOOL_TOKEN="your-school-teacher-jwt"

# Academy teacher token
ACADEMY_TOKEN="your-academy-teacher-jwt"

# Tutor token
TUTOR_TOKEN="your-tutor-jwt"

# Parent token
PARENT_TOKEN="your-parent-jwt"

# Student ID (이민준)
STUDENT_ID="88888888-8888-8888-8888-888888888888"
```

#### Test 3.1: Create Comment (School Teacher)

```bash
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $SCHOOL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-11-01T00:00:00Z",
    "periodEnd": "2025-11-30T23:59:59Z",
    "section": "summary",
    "language": "ko",
    "content": "[TEST] 학교 선생님 테스트 코멘트입니다.",
    "publish": false
  }' | jq

# Expected: 201 Created, response with comment ID
```

#### Test 3.2: List Comments

```bash
curl http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $SCHOOL_TOKEN" | jq

# Expected: List of comments including new draft
```

#### Test 3.3: Update Comment

```bash
COMMENT_ID=1  # Use ID from previous response

curl -X PUT http://localhost:8001/api/teacher/reports/comments/$COMMENT_ID \
  -H "Authorization: Bearer $SCHOOL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "[UPDATED] 학교 선생님 업데이트된 코멘트입니다.",
    "publish": false
  }' | jq

# Expected: 200 OK, updated comment
```

#### Test 3.4: Publish Comment

```bash
curl -X PUT http://localhost:8001/api/teacher/reports/comments/$COMMENT_ID/publish \
  -H "Authorization: Bearer $SCHOOL_TOKEN" | jq

# Expected: 200 OK, isPublished=true
```

#### Test 3.5: Create Academy Comment

```bash
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $ACADEMY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-11-01T00:00:00Z",
    "periodEnd": "2025-11-30T23:59:59Z",
    "section": "summary",
    "language": "ko",
    "content": "[TEST] 학원 강사 테스트 코멘트입니다.",
    "publish": true
  }' | jq

# Expected: 201 Created, sourceType="academy_teacher"
```

#### Test 3.6: Create Tutor Comment

```bash
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $TUTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-11-01T00:00:00Z",
    "periodEnd": "2025-11-30T23:59:59Z",
    "section": "parent_guidance",
    "language": "ko",
    "content": "[TEST] 개인 튜터 학부모 가이드입니다.",
    "publish": true
  }' | jq

# Expected: 201 Created, sourceType="tutor"
```

### Test 4: Parent Report JSON API

```bash
# Get report data (JSON)
curl http://localhost:8001/api/parent/reports/$STUDENT_ID?period=last4w \
  -H "Authorization: Bearer $PARENT_TOKEN" | jq

# Expected response structure:
# {
#   "studentId": "...",
#   "periodStart": "...",
#   "periodEnd": "...",
#   "parentFriendlySummaryKo": "...",
#   "subjects": [
#     {
#       "subjectLabelKo": "수학",
#       "theta": 0.85,
#       "thetaBand": "A",
#       "percentile": 80,
#       ...
#     }
#   ],
#   "schoolTeacherCommentKo": "최근 4주 동안...",
#   "tutorCommentKo": "SAT 대비 과정에서...",
#   "nextPlansKo": [
#     "수학: 난이도 중상 문제...",
#     "주 3회 모의고사..."
#   ],
#   "parentGuidanceKo": "자녀의 학습 패턴을..."
# }
```

**Validation Checklist**:
- [ ] `subjects` array contains 3 items (math, english, science)
- [ ] `schoolTeacherCommentKo` is NOT null (published school comment exists)
- [ ] `tutorCommentKo` is NOT null (published tutor comment exists)
- [ ] `nextPlansKo` array length ≥ 2 (school + academy plans)
- [ ] `parentGuidanceKo` is NOT null

### Test 5: Parent Report PDF API

```bash
# Download PDF
curl http://localhost:8001/api/parent/reports/$STUDENT_ID/pdf?period=last4w \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -o test_report.pdf

# Verify PDF
file test_report.pdf
# Expected: PDF document, version 1.x

# Open PDF (Linux)
xdg-open test_report.pdf

# Open PDF (macOS)
open test_report.pdf
```

**PDF Visual Inspection Checklist**:
- [ ] Header shows student name, school, grade, report period
- [ ] Section 1: Parent-friendly summary in Korean
- [ ] Section 2: Subject table with 3 rows (math, english, science)
  - [ ] Columns: Subject, Band, Percentile, ΔΘ4w, Risk Level
  - [ ] Color-coded risk badges (green/yellow/red)
- [ ] Section 3: Trend chart image (placeholder or real chart)
- [ ] Section 4: School teacher comment (Korean)
- [ ] Section 5: Academy/tutor comment (Korean)
- [ ] Section 6: Next 4-week plans (bullet list, multiple sources)
- [ ] Section 7: Parent guidance (Korean)
- [ ] Footer: DreamSeedAI branding

### Test 6: Student Dashboard API

```bash
# Get ability summary
curl http://localhost:8001/api/abilities/me/summary \
  -H "Authorization: Bearer $STUDENT_TOKEN" | jq

# Expected:
# {
#   "studentId": "...",
#   "asOf": "...",
#   "subjects": [
#     {
#       "subject": "math",
#       "theta": 0.85,
#       "thetaBand": "A",
#       "percentile": 80,
#       "deltaTheta7d": 0.05,
#       "riskLevel": "low",
#       "statusLabel": "🌟 안정적 성장 중",
#       "recommendedAction": "현재 수준을 유지하면서..."
#     }
#   ]
# }

# Get theta trend
curl "http://localhost:8001/api/abilities/me/trend?subject=math&days=60" \
  -H "Authorization: Bearer $STUDENT_TOKEN" | jq

# Expected:
# {
#   "subject": "math",
#   "points": [
#     {
#       "calibratedAt": "2025-11-18T...",
#       "theta": 0.85,
#       "thetaSe": 0.25
#     }
#   ]
# }
```

### Test 7: Tutor Priority List API

```bash
# Get priority list (tutor must be logged in with academy/tutor org)
curl "http://localhost:8001/api/tutor/priorities?subject=math&windowDays=14&limit=10" \
  -H "Authorization: Bearer $TUTOR_TOKEN" | jq

# Expected:
# {
#   "subject": "math",
#   "generatedAt": "...",
#   "windowDays": 14,
#   "students": [
#     {
#       "studentId": "aaaaaaaa-...",
#       "studentName": "Student aaaaaaaa",
#       "theta": -0.75,
#       "thetaBand": "D",
#       "deltaTheta14d": -0.20,
#       "priorityScore": 8.5,
#       "riskLevel": "high",
#       "flags": ["recent_decline", "high_uncertainty"],
#       "recommendedFocus": [
#         "기초 개념 재정리",
#         "최근 틀린 문제 유형 복습"
#       ]
#     }
#   ]
# }
```

**Validation Checklist**:
- [ ] Students sorted by `priorityScore` DESC
- [ ] At-risk student (박지호, θ=-0.75) appears first
- [ ] High-performer (이민준, θ=0.85) appears last or not at all (low priority)
- [ ] `flags` array contains expected flags (recent_decline, high_uncertainty)

---

## ✅ Error Handling Tests

### Test 8: Authorization Failures

```bash
# School teacher tries to access tutor endpoint
curl "http://localhost:8001/api/tutor/priorities?subject=math" \
  -H "Authorization: Bearer $SCHOOL_TOKEN"

# Expected: 403 Forbidden, "Tutor/academy membership required"

# Student tries to access teacher endpoint
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Expected: 403 Forbidden, "Teacher role required"
```

### Test 9: Invalid Period

```bash
# Period too long (> 12 weeks)
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $SCHOOL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-01-01T00:00:00Z",
    "periodEnd": "2025-06-01T00:00:00Z",
    "section": "summary",
    "language": "ko",
    "content": "Test",
    "publish": false
  }'

# Expected: 400 Bad Request, "Report period cannot exceed 12 weeks"
```

### Test 10: Comment Ownership

```bash
# Academy teacher tries to edit school teacher's comment
curl -X PUT http://localhost:8001/api/teacher/reports/comments/1 \
  -H "Authorization: Bearer $ACADEMY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Trying to edit..."
  }'

# Expected: 403 Forbidden, "You can only edit your own comments"
```

---

## ✅ Performance Tests

### Test 11: Query Performance

```bash
# Measure parent report query time
time curl http://localhost:8001/api/parent/reports/$STUDENT_ID?period=last4w \
  -H "Authorization: Bearer $PARENT_TOKEN" -o /dev/null

# Target: < 500ms for JSON response

# Measure PDF generation time
time curl http://localhost:8001/api/parent/reports/$STUDENT_ID/pdf?period=last4w \
  -H "Authorization: Bearer $PARENT_TOKEN" -o /dev/null

# Target: < 2s for PDF generation (with charts)
```

### Test 12: Concurrent Requests

```bash
# Use Apache Bench or similar
ab -n 100 -c 10 \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  "http://localhost:8001/api/parent/reports/$STUDENT_ID?period=last4w"

# Monitor: Response time distribution, error rate
```

---

## ✅ Integration Tests

### Test 13: End-to-End Parent Report Flow

**Scenario**: Complete workflow from comment creation to PDF download

1. **School teacher** creates + publishes summary comment
2. **Academy teacher** creates + publishes next_4w_plan comment
3. **Tutor** creates + publishes parent_guidance comment
4. **Parent** requests PDF
5. **Verify** PDF contains all 3 sources correctly labeled

```bash
# Step 1: School teacher
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $SCHOOL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-12-01T00:00:00Z",
    "periodEnd": "2025-12-31T23:59:59Z",
    "section": "summary",
    "language": "ko",
    "content": "12월 종합 소견: 수학 실력 향상...",
    "publish": true
  }'

# Step 2: Academy teacher
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $ACADEMY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-12-01T00:00:00Z",
    "periodEnd": "2025-12-31T23:59:59Z",
    "section": "next_4w_plan",
    "language": "ko",
    "content": "다음 달 계획: 주 2회 모의고사...",
    "publish": true
  }'

# Step 3: Tutor
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $TUTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-12-01T00:00:00Z",
    "periodEnd": "2025-12-31T23:59:59Z",
    "section": "parent_guidance",
    "language": "ko",
    "content": "학부모님께: 가정에서 복습 시간 확보...",
    "publish": true
  }'

# Step 4: Parent downloads PDF
curl http://localhost:8001/api/parent/reports/$STUDENT_ID/pdf?period=last4w \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -o december_report.pdf

# Step 5: Verify PDF
# - Check "학교 선생님 의견": "12월 종합 소견..."
# - Check "학원 강사 의견": (empty, only plan)
# - Check "다음 4주 계획": "다음 달 계획..."
# - Check "학부모 가이드": "학부모님께: 가정에서..."
```

---

## ✅ Cleanup

### Test 14: Delete Test Data

```bash
# Delete test comments
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "DELETE FROM report_comments WHERE content LIKE '[TEST]%';"

# Delete test abilities (optional, if needed for fresh start)
psql ... -c "DELETE FROM irt_student_abilities WHERE user_id IN ('88888888-8888-8888-8888-888888888888', ...);"

# Keep organizations for next test run
```

---

## 📊 Success Criteria

### Minimum Viable Alpha (Week 4)

- [ ] **Database**: All migrations applied, 4 tables + 4 enums created
- [ ] **Seed Data**: 3 orgs, 3-5 students, 3-7 abilities, 5+ comments
- [ ] **Comment API**: 5 endpoints work (create, list, update, publish, delete)
- [ ] **Authorization**: School/tutor filtering works correctly
- [ ] **Parent Report JSON**: Returns correct multi-source comment aggregation
- [ ] **Parent Report PDF**: Generates valid PDF with all sections
- [ ] **Student Dashboard API**: Returns ability summary + trend
- [ ] **Tutor Priority API**: Returns sorted priority list
- [ ] **Error Handling**: 403/400 responses for invalid requests
- [ ] **Performance**: < 500ms JSON, < 2s PDF

### Blockers (Fix Before UI Integration)

- ❌ User model integration (replace placeholder UUIDs)
- ❌ Parent-child relationship verification (ownership check)
- ❌ Teacher-student assignment filtering (priority list scope)
- ❌ Trend chart generation (matplotlib PNG, not placeholder)

---

## 🚀 Next Steps

After backend testing passes:

1. **Frontend Integration** (Week 4 Day 3-5)
   - Student dashboard: Fetch `/abilities/me/summary`, render cards
   - Tutor dashboard: Fetch `/tutor/priorities`, render table + comment form
   - Parent portal: Fetch `/parent/reports/{id}/pdf`, download button

2. **Alpha User Testing** (Week 4 Day 6-7)
   - Invite 1-2 teachers, 1 tutor, 3 students, 2 parents
   - Run complete workflow: CAT exam → θ calibration → comments → PDF
   - Collect feedback on UX, performance, bugs

3. **Production Deployment** (Week 5)
   - Deploy to staging environment
   - Run smoke tests
   - Deploy to production
   - Monitor logs, performance metrics

---

**Test Execution Date**: ___________  
**Tester**: ___________  
**Results**: ___________
