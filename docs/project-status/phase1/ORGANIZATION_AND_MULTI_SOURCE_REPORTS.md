## 3-Axis Organization Architecture Implementation Guide

**Date**: November 25, 2025  
**Phase**: 1A Extended - Organization & Multi-Source Report Comments  
**Status**: ✅ Complete - Ready for Testing

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Schema](#database-schema)
4. [FastAPI Dependencies](#fastapi-dependencies)
5. [API Endpoints](#api-endpoints)
6. [Parent Report Builder](#parent-report-builder)
7. [Frontend Integration](#frontend-integration)
8. [Testing Plan](#testing-plan)
9. [Deployment Checklist](#deployment-checklist)

---

## Executive Summary

### What's New

This implementation adds a **3-axis permission structure** to DreamSeedAI:

1. **User Type Axis** (existing): student, teacher, parent, admin
2. **Organization Type Axis** (NEW): public_school, private_school, academy, tutoring_center, private_tutor
3. **Organization Role Axis** (NEW): org_admin, org_head_teacher, org_teacher, org_assistant

### Key Features

- **Multi-organization membership**: Teachers can work at multiple schools/academies simultaneously
- **Multi-source student enrollment**: Students can attend school + academy + private tutor concurrently
- **Multi-source report comments**: School teachers and tutors contribute separate sections to parent reports
- **Role-based API access**: Separate endpoints for school teachers vs tutors with automatic org-type filtering
- **Bilingual parent reports**: Korean primary + English secondary with source-separated comments

### Components Delivered

| Component | File | Status | Lines |
|-----------|------|--------|-------|
| Organization models | backend/app/models/org_models.py | ✅ Complete | ~250 |
| Report comment models | backend/app/models/report_models.py | ✅ Complete | ~250 |
| Alembic migration | backend/alembic/versions/003_org_and_comments.py | ✅ Complete | ~150 |
| FastAPI dependencies | backend/app/core/security.py | ✅ Updated | +150 |
| Report comment API | backend/app/routers/report_comments.py | ✅ Complete | ~500 |
| Parent report builder | backend/app/services/parent_report_builder.py | ✅ Complete | ~450 |
| Updated schemas | backend/app/schemas/ability_schemas.py | ✅ Updated | ~10 |
| Integration docs | This file | ✅ Complete | ~1000 |

**Total**: ~2,500 lines of production code + comprehensive documentation

---

## Architecture Overview

### Conceptual Model

```
User (role: teacher, student, parent, admin)
  ↓
OrgMembership (school, academy, tutor)
  ↓
Organization (public_school, private_school, academy, etc.)
  ↓
ReportComment (SCHOOL_TEACHER, ACADEMY_TEACHER, TUTOR)
  ↓
ParentReport (ability data + multi-source comments)
```

### Data Flow Example

**Student Journey**:
```
Student: 이민준 (Lee Min-jun)
├─ Enrollment 1: 서울고등학교 (public_school) - Class 2-3
├─ Enrollment 2: 대치학원 (academy) - SAT Prep Group A
└─ Enrollment 3: 김튜터 (private_tutor) - 1:1 Math

IRT Abilities (irt_student_abilities):
├─ Math: θ=0.85, SE=0.25 (calibrated 2025-11-20)
├─ English: θ=0.42, SE=0.30 (calibrated 2025-11-18)
└─ Science: θ=-0.15, SE=0.35 (calibrated 2025-11-19)

Report Comments (report_comments):
├─ 서울고등학교 담임 (SCHOOL_TEACHER):
│   ├─ SUMMARY (ko): "최근 4주 동안 수학 실력이 꾸준히 향상되었습니다..."
│   ├─ NEXT_4W_PLAN (ko): "수학: 난이도 중상 문제 집중 연습..."
│   └─ PARENT_GUIDANCE (ko): "정기적인 격려와 칭찬을 아끼지 마세요..."
├─ 대치학원 강사 (ACADEMY_TEACHER):
│   ├─ SUMMARY (ko): "SAT 대비 과정에서 문제 풀이 속도가 개선되었습니다..."
│   └─ NEXT_4W_PLAN (ko): "주 3회 모의고사 응시 권장..."
└─ 김튜터 (TUTOR):
    ├─ SUMMARY (ko): "1:1 수학 과외에서 기초 개념 정리가 잘 되었습니다..."
    └─ PARENT_GUIDANCE (ko): "가정에서 복습 시간 확보 필요..."

Parent Report PDF:
├─ Section 1: 능력 요약 (from irt_student_abilities)
├─ Section 2: 학교 선생님 의견 (from SCHOOL_TEACHER comments)
├─ Section 3: 학원/튜터 의견 (from ACADEMY_TEACHER + TUTOR comments)
├─ Section 4: 다음 4주 계획 (all NEXT_4W_PLAN comments combined)
└─ Section 5: 학부모 가이드 (PARENT_GUIDANCE, school priority)
```

---

## Database Schema

### Tables Created

#### 1. `organizations`

Educational institutions (schools, academies, tutoring centers).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Organization UUID |
| name | VARCHAR(200) | NOT NULL | Organization name |
| type | organization_type | NOT NULL | ENUM: public_school, private_school, academy, tutoring_center, private_tutor, homeschool |
| external_code | VARCHAR(50) | UNIQUE | School code, business registration number |
| is_active | BOOLEAN | DEFAULT true | Active status |
| created_at | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update timestamp |

**Indexes**:
- `PRIMARY KEY (id)`
- `UNIQUE (external_code)`

**Sample Data**:
```sql
INSERT INTO organizations (id, name, type, external_code)
VALUES 
  ('11111111-1111-1111-1111-111111111111', '서울고등학교', 'public_school', 'SCHOOL-2025-001'),
  ('22222222-2222-2222-2222-222222222222', '대치입시학원', 'academy', 'ACADEMY-2025-042'),
  ('33333333-3333-3333-3333-333333333333', '김튜터 수학교실', 'private_tutor', NULL);
```

#### 2. `org_memberships`

Teacher/admin affiliations with organizations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, SERIAL | Membership ID |
| user_id | UUID | FK → user(id), CASCADE | Teacher/admin UUID |
| organization_id | UUID | FK → organizations(id), CASCADE | Organization UUID |
| role | org_role | NOT NULL | ENUM: org_admin, org_head_teacher, org_teacher, org_assistant |
| created_at | TIMESTAMPTZ | NOT NULL | Membership creation date |

**Constraints**:
- `UNIQUE (user_id, organization_id)`: One role per org
- `FK user_id → user(id) ON DELETE CASCADE`
- `FK organization_id → organizations(id) ON DELETE CASCADE`

**Indexes**:
- `PRIMARY KEY (id)`
- `ix_org_memberships_user_id (user_id)`
- `ix_org_memberships_organization_id (organization_id)`

**Sample Data**:
```sql
-- Teacher at school
INSERT INTO org_memberships (user_id, organization_id, role)
VALUES ('teacher-uuid-1', '11111111-1111-1111-1111-111111111111', 'org_head_teacher');

-- Same teacher also works at academy
INSERT INTO org_memberships (user_id, organization_id, role)
VALUES ('teacher-uuid-1', '22222222-2222-2222-2222-222222222222', 'org_teacher');
```

#### 3. `student_org_enrollments`

Student enrollments in organizations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, SERIAL | Enrollment ID |
| student_id | UUID | FK → user(id), CASCADE | Student UUID |
| organization_id | UUID | FK → organizations(id), CASCADE | Organization UUID |
| label | VARCHAR(100) | NULLABLE | Class/group identifier (e.g., "2-3", "SAT Group A") |
| created_at | TIMESTAMPTZ | NOT NULL | Enrollment date |

**Constraints**:
- `UNIQUE (student_id, organization_id)`: No duplicate enrollments
- `FK student_id → user(id) ON DELETE CASCADE`
- `FK organization_id → organizations(id) ON DELETE CASCADE`

**Indexes**:
- `PRIMARY KEY (id)`
- `ix_student_org_enrollments_student_id (student_id)`
- `ix_student_org_enrollments_organization_id (organization_id)`

**Sample Data**:
```sql
-- Student attends school
INSERT INTO student_org_enrollments (student_id, organization_id, label)
VALUES ('student-uuid-1', '11111111-1111-1111-1111-111111111111', '2-3');

-- Same student attends academy
INSERT INTO student_org_enrollments (student_id, organization_id, label)
VALUES ('student-uuid-1', '22222222-2222-2222-2222-222222222222', 'SAT Prep A');

-- Same student has private tutor
INSERT INTO student_org_enrollments (student_id, organization_id, label)
VALUES ('student-uuid-1', '33333333-3333-3333-3333-333333333333', NULL);
```

#### 4. `report_comments`

Teacher/tutor comments for parent reports.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PK, SERIAL | Comment ID |
| student_id | UUID | FK → user(id), CASCADE | Target student UUID |
| organization_id | UUID | FK → organizations(id), CASCADE | Source organization UUID |
| author_id | UUID | FK → user(id), CASCADE | Comment author UUID |
| source_type | report_source_type | NOT NULL | ENUM: school_teacher, academy_teacher, tutor |
| section | report_section | NOT NULL | ENUM: summary, next_4w_plan, parent_guidance |
| language | VARCHAR(5) | NOT NULL, DEFAULT 'ko' | ISO 639-1 code (ko, en) |
| period_start | TIMESTAMPTZ | NOT NULL | Report period start (inclusive) |
| period_end | TIMESTAMPTZ | NOT NULL | Report period end (inclusive) |
| content | TEXT | NOT NULL | Comment text (Markdown supported) |
| is_published | BOOLEAN | NOT NULL, DEFAULT false | Published status (visible in parent reports) |
| created_at | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update timestamp |

**Constraints**:
- `FK student_id → user(id) ON DELETE CASCADE`
- `FK organization_id → organizations(id) ON DELETE CASCADE`
- `FK author_id → user(id) ON DELETE CASCADE`

**Indexes**:
- `PRIMARY KEY (id)`
- `ix_report_comments_student_period (student_id, period_start, is_published)`: Parent report queries
- `ix_report_comments_organization_period (organization_id, period_start)`: Org-level reports
- `ix_report_comments_author_id (author_id)`: Teacher comment history

**Sample Data**:
```sql
-- School teacher comment (published)
INSERT INTO report_comments (
  student_id, organization_id, author_id, source_type, section, language,
  period_start, period_end, content, is_published
)
VALUES (
  'student-uuid-1', '11111111-1111-1111-1111-111111111111', 'teacher-uuid-1',
  'school_teacher', 'summary', 'ko',
  '2025-11-01', '2025-11-30',
  '최근 4주 동안 수학 실력이 꾸준히 향상되었습니다...',
  true
);

-- Academy teacher comment (draft)
INSERT INTO report_comments (
  student_id, organization_id, author_id, source_type, section, language,
  period_start, period_end, content, is_published
)
VALUES (
  'student-uuid-1', '22222222-2222-2222-2222-222222222222', 'teacher-uuid-2',
  'academy_teacher', 'summary', 'ko',
  '2025-11-01', '2025-11-30',
  'SAT 대비 과정에서 문제 풀이 속도가 개선되었습니다...',
  false
);
```

### Enums Created

```sql
CREATE TYPE organization_type AS ENUM (
  'public_school',
  'private_school',
  'academy',
  'tutoring_center',
  'private_tutor',
  'homeschool'
);

CREATE TYPE org_role AS ENUM (
  'org_admin',
  'org_head_teacher',
  'org_teacher',
  'org_assistant'
);

CREATE TYPE report_source_type AS ENUM (
  'school_teacher',
  'academy_teacher',
  'tutor'
);

CREATE TYPE report_section AS ENUM (
  'summary',
  'next_4w_plan',
  'parent_guidance'
);
```

---

## FastAPI Dependencies

### Dependency Hierarchy

```
get_current_user()  (FastAPI-Users, all roles)
  ↓
get_current_teacher()  (role="teacher" only)
  ↓
get_current_teacher_with_memberships()  (teacher + OrgMembership[])
  ↓
  ├─ get_current_school_teacher()  (PUBLIC_SCHOOL | PRIVATE_SCHOOL)
  ├─ get_current_tutor()  (ACADEMY | TUTORING_CENTER | PRIVATE_TUTOR)
  └─ get_current_teacher_any_org()  (any org type)
```

### Implementation

**File**: `backend/app/core/security.py`

#### 1. `get_current_teacher_with_memberships()`

```python
async def get_current_teacher_with_memberships(
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_async_session),
) -> tuple[User, list[OrgMembership]]:
    """
    Get teacher with their organization memberships.
    
    Returns:
        Tuple of (user, memberships list)
    """
    result = await db.execute(
        select(OrgMembership)
        .where(OrgMembership.user_id == current_user.id)
        .options(selectinload(OrgMembership.organization))
    )
    memberships = result.scalars().all()
    return current_user, memberships
```

#### 2. `get_current_school_teacher()`

```python
async def get_current_school_teacher(
    data: tuple[User, list[OrgMembership]] = Depends(get_current_teacher_with_memberships),
) -> tuple[User, Organization, OrgMembership]:
    """
    Require teacher with school organization membership.
    
    Filters for:
    - Organization type: PUBLIC_SCHOOL or PRIVATE_SCHOOL
    - Organization role: ORG_TEACHER, ORG_HEAD_TEACHER, or ORG_ADMIN
    
    Raises:
        HTTPException 403: If teacher has no school memberships
    """
    user, memberships = data
    
    for m in memberships:
        org = m.organization
        if is_school_org(org.type) and m.role in (
            OrgRole.ORG_TEACHER,
            OrgRole.ORG_HEAD_TEACHER,
            OrgRole.ORG_ADMIN,
        ):
            return user, org, m
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="School teacher membership required.",
    )
```

#### 3. `get_current_tutor()`

```python
async def get_current_tutor(
    data: tuple[User, list[OrgMembership]] = Depends(get_current_teacher_with_memberships),
) -> tuple[User, Organization, OrgMembership]:
    """
    Require teacher with tutoring organization membership.
    
    Filters for:
    - Organization type: ACADEMY, TUTORING_CENTER, or PRIVATE_TUTOR
    - Organization role: ORG_TEACHER, ORG_HEAD_TEACHER, or ORG_ADMIN
    
    Raises:
        HTTPException 403: If teacher has no tutoring organization memberships
    """
    user, memberships = data
    
    for m in memberships:
        org = m.organization
        if is_tutoring_org(org.type) and m.role in (
            OrgRole.ORG_TEACHER,
            OrgRole.ORG_HEAD_TEACHER,
            OrgRole.ORG_ADMIN,
        ):
            return user, org, m
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tutor/academy membership required.",
    )
```

### Usage Examples

```python
# School-only endpoint
@router.get("/school/report")
async def school_report(
    context: tuple[User, Organization, OrgMembership] = Depends(get_current_school_teacher),
):
    user, org, membership = context
    # Only teachers from schools can access this

# Tutor-only endpoint
@router.get("/tutor/priorities")
async def tutor_priorities(
    context: tuple[User, Organization, OrgMembership] = Depends(get_current_tutor),
):
    user, org, membership = context
    # Only tutors/academy teachers can access this

# Any teacher endpoint
@router.post("/teacher/reports/{student_id}/comments")
async def create_comment(
    student_id: uuid.UUID,
    context: tuple[User, Organization, OrgMembership] = Depends(get_current_teacher_any_org),
):
    user, org, membership = context
    # Both school teachers and tutors can access this
```

---

## API Endpoints

### Report Comment Endpoints

**File**: `backend/app/routers/report_comments.py`

#### 1. POST `/api/teacher/reports/{student_id}/comments`

Create a new report comment.

**Authorization**: `get_current_teacher_any_org`

**Request Body**:
```json
{
  "studentId": "123e4567-e89b-12d3-a456-426614174000",
  "periodStart": "2025-11-01T00:00:00Z",
  "periodEnd": "2025-11-30T23:59:59Z",
  "section": "summary",
  "language": "ko",
  "content": "최근 4주 동안 수학 실력이 꾸준히 향상되었습니다...",
  "publish": false
}
```

**Response**: `201 Created`
```json
{
  "id": 123,
  "studentId": "123e4567-e89b-12d3-a456-426614174000",
  "organizationId": "789e4567-e89b-12d3-a456-426614174000",
  "authorId": "456e4567-e89b-12d3-a456-426614174000",
  "sourceType": "school_teacher",
  "section": "summary",
  "language": "ko",
  "periodStart": "2025-11-01T00:00:00Z",
  "periodEnd": "2025-11-30T23:59:59Z",
  "content": "최근 4주 동안...",
  "isPublished": false,
  "createdAt": "2025-11-25T10:00:00Z",
  "updatedAt": "2025-11-25T10:00:00Z"
}
```

**Business Logic**:
- Validates period (≤ 12 weeks, not in future)
- Determines `source_type` from `org.type`:
  * `public_school`, `private_school` → `SCHOOL_TEACHER`
  * `academy`, `tutoring_center` → `ACADEMY_TEACHER`
  * `private_tutor` → `TUTOR`
- Allows multiple comments for same (student, period, section) from different sources

#### 2. GET `/api/teacher/reports/{student_id}/comments`

List report comments for a student.

**Authorization**: `get_current_teacher_any_org`

**Query Parameters**:
- `period_start` (optional): Filter by period start
- `period_end` (optional): Filter by period end
- `section` (optional): Filter by section (summary, next_4w_plan, parent_guidance)
- `published_only` (default: false): Show only published comments

**Response**: `200 OK`
```json
{
  "total": 3,
  "comments": [
    {
      "id": 123,
      "studentId": "...",
      "section": "summary",
      "content": "...",
      "isPublished": true,
      ...
    },
    ...
  ]
}
```

#### 3. PUT `/api/teacher/reports/comments/{comment_id}`

Update an existing comment.

**Authorization**: Comment author only

**Request Body** (partial update):
```json
{
  "content": "Updated content...",
  "language": "ko",
  "publish": true
}
```

#### 4. PUT `/api/teacher/reports/comments/{comment_id}/publish`

Publish a comment (shortcut for `publish=true`).

**Authorization**: Comment author only

#### 5. DELETE `/api/teacher/reports/comments/{comment_id}`

Delete a comment.

**Authorization**: Comment author only

**Response**: `204 No Content`

---

## Parent Report Builder

### Service Architecture

**File**: `backend/app/services/parent_report_builder.py`

#### Core Function: `build_parent_report_data()`

```python
async def build_parent_report_data(
    db: AsyncSession,
    student_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
) -> ParentReportData:
    """
    Build complete parent report data structure.
    
    Combines:
    1. Ability summaries (per subject) from irt_student_abilities
    2. Published comments from school teachers (SCHOOL_TEACHER)
    3. Published comments from academy teachers/tutors (ACADEMY_TEACHER, TUTOR)
    4. Next 4-week plans from all sources (NEXT_4W_PLAN section)
    5. Parent guidance (school priority, tutor fallback)
    
    Comment selection logic:
    - School teacher comments take priority over tutors
    - SUMMARY section: Separate school vs tutor comments
    - NEXT_4W_PLAN section: Collect all plans from all sources
    - PARENT_GUIDANCE section: School first, tutor fallback
    - Always use most recent (updated_at DESC) within each category
    """
```

#### Comment Aggregation Logic

**Priority Rules**:
1. **SUMMARY section**: Keep school and tutor comments separate
   - `schoolTeacherCommentKo` ← SCHOOL_TEACHER + SUMMARY + ko
   - `tutorCommentKo` ← ACADEMY_TEACHER or TUTOR + SUMMARY + ko
2. **NEXT_4W_PLAN section**: Combine all sources
   - `nextPlansKo` ← All NEXT_4W_PLAN comments (school first, then tutors, sorted by updated_at DESC)
3. **PARENT_GUIDANCE section**: School priority, tutor fallback
   - `parentGuidanceKo` ← SCHOOL_TEACHER + PARENT_GUIDANCE + ko OR (if not exists) TUTOR + PARENT_GUIDANCE + ko

**Helper Functions**:
```python
def pick_comment(
    comments: list[ReportComment],
    source_type: ReportSourceType,
    section: ReportSection,
    language: str,
) -> Optional[str]:
    """Select most recent comment matching criteria."""

def pick_comment_any_tutor(
    comments: list[ReportComment],
    section: ReportSection,
    language: str,
) -> Optional[str]:
    """Select most recent comment from any tutoring source (academy > private tutor)."""

def collect_all_plans(
    comments: list[ReportComment],
    language: str,
) -> list[str]:
    """Collect all NEXT_4W_PLAN comments (school first, then tutors)."""
```

#### Auto-Generated Summaries

```python
def generate_parent_summary_ko(
    subjects: list[ParentReportSubject],
    period_start: datetime,
    period_end: datetime,
) -> str:
    """
    Generate Korean parent summary from ability data.
    
    Logic:
    - Count subjects by risk level
    - Calculate average delta theta
    - Generate 2-3 sentence summary:
      * At-risk subjects → Warning tone
      * Positive growth → Encouraging tone
      * Stable → Maintenance advice
    """
```

#### Updated ParentReportData Schema

**File**: `backend/app/schemas/ability_schemas.py`

```python
class ParentReportData(BaseModel):
    studentId: str
    periodStart: datetime
    periodEnd: datetime
    parentFriendlySummaryKo: str
    parentFriendlySummaryEn: str
    subjects: List[ParentReportSubject]
    trendChartUrl: str
    
    # NEW: Separated school vs tutor comments
    schoolTeacherCommentKo: Optional[str] = None
    schoolTeacherCommentEn: Optional[str] = None
    tutorCommentKo: Optional[str] = None
    tutorCommentEn: Optional[str] = None
    
    nextPlansKo: List[str] = Field(default_factory=list)
    nextPlansEn: List[str] = Field(default_factory=list)
    parentGuidanceKo: Optional[str] = None
    parentGuidanceEn: Optional[str] = None
```

---

## Frontend Integration

### Teacher Portal - Comment Input UI

**Route**: `/teacher/students/{studentId}/report-comments`

**Components**:
```typescript
// apps/teacher_front/components/ReportCommentForm.tsx

interface ReportCommentFormProps {
  studentId: string;
  organizationType: OrganizationType;
  periodStart: Date;
  periodEnd: Date;
  onSuccess?: () => void;
}

export function ReportCommentForm(props: ReportCommentFormProps) {
  const [section, setSection] = useState<ReportSection>('summary');
  const [language, setLanguage] = useState<'ko' | 'en'>('ko');
  const [content, setContent] = useState('');
  const [publish, setPublish] = useState(false);
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    const response = await fetch(`/api/teacher/reports/${props.studentId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify({
        studentId: props.studentId,
        periodStart: props.periodStart.toISOString(),
        periodEnd: props.periodEnd.toISOString(),
        section,
        language,
        content,
        publish,
      }),
    });
    
    if (response.ok) {
      props.onSuccess?.();
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-4">
        <label>섹션 선택</label>
        <select value={section} onChange={(e) => setSection(e.target.value as ReportSection)}>
          <option value="summary">종합 소견 (Summary)</option>
          <option value="next_4w_plan">다음 4주 계획 (Next 4-Week Plan)</option>
          <option value="parent_guidance">학부모 가이드 (Parent Guidance)</option>
        </select>
      </div>
      
      <div className="mb-4">
        <label>언어</label>
        <select value={language} onChange={(e) => setLanguage(e.target.value as 'ko' | 'en')}>
          <option value="ko">한국어 (Korean)</option>
          <option value="en">English</option>
        </select>
      </div>
      
      <div className="mb-4">
        <label>코멘트 내용</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={10}
          className="w-full border p-2"
          placeholder={section === 'summary' ? '학생의 최근 학습 상태를 요약하세요...' : ''}
        />
      </div>
      
      <div className="mb-4">
        <label>
          <input
            type="checkbox"
            checked={publish}
            onChange={(e) => setPublish(e.target.checked)}
          />
          즉시 발행 (부모 리포트에 표시)
        </label>
      </div>
      
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
        {publish ? '저장 및 발행' : '임시 저장'}
      </button>
    </form>
  );
}
```

### Parent Portal - PDF Download

**Route**: `/parent/children/{childId}/reports`

```typescript
// apps/parent_front/components/ReportList.tsx

export function ReportList({ childId }: { childId: string }) {
  const [period, setPeriod] = useState<'last4w' | 'last8w' | 'last12w'>('last4w');
  
  const handleDownloadPDF = async () => {
    const response = await fetch(
      `/api/parent/reports/${childId}/pdf?period=${period}`,
      {
        headers: { 'Authorization': `Bearer ${getToken()}` },
      }
    );
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${childId}_${period}_${new Date().toISOString().split('T')[0]}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };
  
  return (
    <div>
      <select value={period} onChange={(e) => setPeriod(e.target.value as any)}>
        <option value="last4w">최근 4주</option>
        <option value="last8w">최근 8주</option>
        <option value="last12w">최근 12주</option>
      </select>
      
      <button onClick={handleDownloadPDF} className="ml-4 bg-blue-500 text-white px-4 py-2">
        리포트 다운로드 (PDF)
      </button>
    </div>
  );
}
```

---

## Testing Plan

### 1. Database Migration Testing

```bash
# Apply migration
cd backend
alembic upgrade head

# Verify tables
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "\dt"

# Expected output:
#   organizations
#   org_memberships
#   student_org_enrollments
#   report_comments

# Verify enums
psql ... -c "\dT"

# Expected output:
#   organization_type
#   org_role
#   report_source_type
#   report_section

# Verify indexes
psql ... -c "\di ix_org_*"
psql ... -c "\di ix_student_org_*"
psql ... -c "\di ix_report_comments_*"
```

### 2. Seed Test Data

**Script**: `scripts/seed_org_and_comments.py`

```python
"""Seed organizations, memberships, enrollments, and comments."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.org_models import Organization, OrgMembership, StudentOrgEnrollment, OrganizationType, OrgRole
from app.models.report_models import ReportComment, ReportSection, ReportSourceType

async def seed_data():
    async for db in get_async_session():
        # Create organizations
        school = Organization(
            id=uuid.UUID('11111111-1111-1111-1111-111111111111'),
            name='서울고등학교',
            type=OrganizationType.PUBLIC_SCHOOL,
            external_code='SCHOOL-2025-001',
        )
        academy = Organization(
            id=uuid.UUID('22222222-2222-2222-2222-222222222222'),
            name='대치입시학원',
            type=OrganizationType.ACADEMY,
            external_code='ACADEMY-2025-042',
        )
        tutor = Organization(
            id=uuid.UUID('33333333-3333-3333-3333-333333333333'),
            name='김튜터 수학교실',
            type=OrganizationType.PRIVATE_TUTOR,
        )
        
        db.add_all([school, academy, tutor])
        await db.commit()
        
        # Create teacher memberships (TODO: Use real teacher UUIDs)
        # membership1 = OrgMembership(...)
        
        # Create student enrollments (TODO: Use real student UUIDs)
        # enrollment1 = StudentOrgEnrollment(...)
        
        # Create report comments (TODO: Use real user/org UUIDs)
        # comment1 = ReportComment(...)
        
        print("✅ Seed data created successfully")

if __name__ == "__main__":
    asyncio.run(seed_data())
```

### 3. API Testing

**Test Report Comment Creation**:
```bash
TOKEN="your-teacher-jwt-token"
STUDENT_ID="student-uuid"

# Create draft comment
curl -X POST http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "studentId": "'$STUDENT_ID'",
    "periodStart": "2025-11-01T00:00:00Z",
    "periodEnd": "2025-11-30T23:59:59Z",
    "section": "summary",
    "language": "ko",
    "content": "테스트 코멘트입니다...",
    "publish": false
  }'

# List comments
curl http://localhost:8001/api/teacher/reports/$STUDENT_ID/comments \
  -H "Authorization: Bearer $TOKEN"

# Publish comment
curl -X PUT http://localhost:8001/api/teacher/reports/comments/1/publish \
  -H "Authorization: Bearer $TOKEN"
```

**Test Parent Report PDF**:
```bash
TOKEN="your-parent-jwt-token"
STUDENT_ID="student-uuid"

# Get JSON data
curl http://localhost:8001/api/parent/reports/$STUDENT_ID?period=last4w \
  -H "Authorization: Bearer $TOKEN" | jq

# Download PDF
curl http://localhost:8001/api/parent/reports/$STUDENT_ID/pdf?period=last4w \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf
```

### 4. Unit Tests

**Test Comment Aggregation**:
```python
# tests/test_parent_report_builder.py

import pytest
from datetime import datetime, timedelta

from app.services.parent_report_builder import (
    pick_comment,
    pick_comment_any_tutor,
    collect_all_plans,
)
from app.models.report_models import ReportComment, ReportSection, ReportSourceType

def test_pick_comment_school_teacher():
    """Test picking school teacher comment from list."""
    comments = [
        ReportComment(
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.SUMMARY,
            language='ko',
            content='School comment',
            updated_at=datetime(2025, 11, 25, 12, 0),
        ),
        ReportComment(
            source_type=ReportSourceType.TUTOR,
            section=ReportSection.SUMMARY,
            language='ko',
            content='Tutor comment',
            updated_at=datetime(2025, 11, 25, 14, 0),
        ),
    ]
    
    result = pick_comment(
        comments, ReportSourceType.SCHOOL_TEACHER, ReportSection.SUMMARY, 'ko'
    )
    
    assert result == 'School comment'

def test_collect_all_plans():
    """Test collecting all NEXT_4W_PLAN comments."""
    comments = [
        ReportComment(
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.NEXT_4W_PLAN,
            language='ko',
            content='Plan 1 (school)',
        ),
        ReportComment(
            source_type=ReportSourceType.TUTOR,
            section=ReportSection.NEXT_4W_PLAN,
            language='ko',
            content='Plan 2 (tutor)',
        ),
    ]
    
    plans = collect_all_plans(comments, 'ko')
    
    assert len(plans) == 2
    assert 'Plan 1 (school)' in plans
    assert 'Plan 2 (tutor)' in plans
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] **Run Alembic migration** (003_org_and_comments.py)
- [ ] **Verify database schema** (tables, indexes, enums)
- [ ] **Seed test data** (organizations, memberships, enrollments)
- [ ] **Test API endpoints** (create, list, update, publish, delete comments)
- [ ] **Test parent report PDF generation** (with multi-source comments)
- [ ] **Code review** (org_models, report_models, security dependencies, report_comments router)
- [ ] **Documentation review** (this guide + API spec)

### Production Deployment

- [ ] **Backup database** (pre-migration)
- [ ] **Apply migration** (alembic upgrade head)
- [ ] **Verify migration success** (\dt, \dT, \di)
- [ ] **Deploy backend code** (restart FastAPI service)
- [ ] **Health check** (GET /health)
- [ ] **Smoke test** (create/list/publish comments)
- [ ] **Monitor logs** (check for migration errors, constraint violations)

### Post-Deployment

- [ ] **Create seed organizations** (via admin panel or SQL)
- [ ] **Assign teacher memberships** (link existing teachers to orgs)
- [ ] **Assign student enrollments** (link existing students to orgs)
- [ ] **User training** (teacher comment workflow, parent PDF download)
- [ ] **Performance monitoring** (query times, PDF generation latency)

---

## Appendices

### A. OrganizationType → ReportSourceType Mapping

| OrganizationType | ReportSourceType | PDF Section Header |
|------------------|------------------|-------------------|
| PUBLIC_SCHOOL | SCHOOL_TEACHER | "학교 선생님 의견" |
| PRIVATE_SCHOOL | SCHOOL_TEACHER | "학교 선생님 의견" |
| ACADEMY | ACADEMY_TEACHER | "학원 강사 의견" |
| TUTORING_CENTER | ACADEMY_TEACHER | "튜터 센터 의견" |
| PRIVATE_TUTOR | TUTOR | "개인 튜터 의견" |
| HOMESCHOOL | TUTOR | "홈스쿨 교사 의견" |

### B. ReportSection Usage Guidelines

| Section | Purpose | Example (Korean) | Example (English) |
|---------|---------|------------------|-------------------|
| SUMMARY | Overall assessment (1-3 paragraphs) | "최근 4주 동안 수학 실력이 꾸준히 향상되었습니다..." | "During the past 4 weeks, math skills have steadily improved..." |
| NEXT_4W_PLAN | Recommended activities (bullet points) | "1. 기초 개념 복습 (주 3회, 각 30분)" | "1. Review basic concepts (3x/week, 30 min each)" |
| PARENT_GUIDANCE | Advice for parents (1-2 paragraphs) | "정기적인 격려와 칭찬을 아끼지 마세요..." | "Provide regular encouragement and praise..." |

### C. Known Limitations & TODOs

**Database**:
- [ ] User model integration (user_id FK relationships currently TODO)
- [ ] Parent-child relationship table (verify parent can access child's reports)
- [ ] Teacher-student assignment table (filter priority list to assigned students)

**API**:
- [ ] Org admin can edit any comments from their org (currently author-only)
- [ ] Bulk comment creation (multi-student, same period)
- [ ] Comment templates (pre-filled content for common scenarios)
- [ ] AI-generated comment suggestions (GPT-4 based on ability data)

**Frontend**:
- [ ] Teacher comment editor UI (Week 4)
- [ ] Parent report dashboard (Week 4)
- [ ] Organization management admin panel (Week 5)
- [ ] Tutor-student assignment workflow (Week 5)

**Performance**:
- [ ] Comment caching (Redis, invalidate on publish/update)
- [ ] PDF generation async queue (Celery + S3 storage)
- [ ] Report data pre-aggregation (materialized view for common periods)

---

## Contact & Support

**Implementation Date**: November 25, 2025  
**Phase**: 1A Extended - Organization Architecture  
**Author**: GitHub Copilot + User Collaboration  
**Status**: ✅ Complete - Ready for Testing

For questions or issues, refer to:
- Main dashboard guide: `docs/project-status/phase1/STUDENT_TUTOR_PARENT_DASHBOARDS.md`
- IRT/CAT pipeline guide: `docs/project-status/phase1/IRT_CAT_PRODUCTION_PIPELINE.md`
- Backend API guide: `backend/API_GUIDE.md`

---

**End of Document**
