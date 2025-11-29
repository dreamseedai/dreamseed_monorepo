# Phase 2.0 - Aptitude & Interest Assessment (적성/흥미 검사)

**Date:** November 24, 2025  
**Status:** 📋 Planning (Implementation: Phase 2.0)  
**Priority:** 🟪 **CORE FEATURE** - Equal to Academic CAT  

---

## 🎯 Strategic Positioning

### DreamSeed AI = Two Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    DreamSeed AI Platform                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🧮 Pillar 1: Academic Achievement                         │
│     └─ CAT/IRT Adaptive Testing                            │
│        └─ Math, English, Science                           │
│        └─ Ability estimation (θ)                           │
│        └─ Diagnostic feedback                              │
│                                                             │
│  🎨 Pillar 2: Aptitude & Interest Profiling               │
│     └─ Career/Major Guidance                               │
│        └─ STEM vs Humanities vs Arts                       │
│        └─ Learning style preferences                       │
│        └─ Interest/personality dimensions                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Why This Matters:**
- Academic tests only measure **what students know**
- Aptitude tests reveal **what students are good at**
- Interest surveys show **what students enjoy**
- Combined → **Personalized career/major recommendations**

**Phase Timeline:**
- Phase 1.0: Math CAT only (Academic pillar foundation)
- Phase 1.5: English/Science CAT (Academic pillar complete)
- **Phase 2.0: Aptitude Assessment (Second pillar launch)** ⬅️ THIS
- Phase 2.5: Combined insights (Both pillars integrated)

---

## 📊 Aptitude Dimensions Framework

### Proposed Dimension Model

DreamSeed AI will use a **hybrid model** combining:
- Holland Code (RIASEC) - Career interests
- Big Five - Personality traits
- STEM/Non-STEM aptitude - Academic strengths
- Learning style preferences - Study habits

**Core Dimensions (v1):**

| Dimension | Range | Description | Example Questions |
|-----------|-------|-------------|-------------------|
| **STEM_interest** | -1 to +1 | 이공계 흥미도 | "수학 문제 풀기가 즐겁다" |
| **Verbal_aptitude** | -1 to +1 | 언어적 사고력 | "글쓰기로 생각을 표현하는 게 편하다" |
| **Artistic_creativity** | -1 to +1 | 예술적 창의성 | "새로운 디자인/작품을 만드는 게 좋다" |
| **Social_orientation** | -1 to +1 | 사회적 지향성 | "사람들과 함께 일하는 게 좋다" |
| **Practical_hands_on** | -1 to +1 | 실무/실습 선호 | "실제로 만들어보는 활동이 좋다" |
| **Logical_reasoning** | -1 to +1 | 논리적 사고력 | "복잡한 문제를 분석하는 게 재미있다" |

**Composite Scores (derived):**
- **Engineering_fit** = 0.6 × STEM + 0.4 × Logical - 0.2 × Social
- **Business_fit** = 0.5 × Social + 0.3 × Verbal + 0.2 × Practical
- **Humanities_fit** = 0.6 × Verbal + 0.3 × Artistic - 0.3 × STEM
- **Arts_fit** = 0.7 × Artistic + 0.2 × Verbal + 0.1 × Social

---

## 🗄️ Database Schema

### Core Tables

```sql
-- Aptitude survey definitions
CREATE TABLE aptitude_surveys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,  -- "STEM Aptitude v1"
    description TEXT,
    target_age_min INTEGER,  -- 13 (middle school)
    target_age_max INTEGER,  -- 18 (high school)
    language VARCHAR(10) DEFAULT 'ko',
    total_questions INTEGER NOT NULL,
    estimated_time_min INTEGER,  -- 15 minutes
    active BOOLEAN DEFAULT true,
    version VARCHAR(20),  -- "1.0.0"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Survey questions
CREATE TABLE aptitude_questions (
    id BIGSERIAL PRIMARY KEY,
    survey_id INTEGER REFERENCES aptitude_surveys(id) ON DELETE CASCADE,
    question_num INTEGER NOT NULL,  -- 1, 2, 3, ...
    question_text TEXT NOT NULL,
    dimension VARCHAR(50) NOT NULL,  -- 'STEM_interest', 'Verbal_aptitude', ...
    item_type VARCHAR(20) DEFAULT 'likert',  -- 'likert', 'forced_choice', 'ranking'
    reverse_scored BOOLEAN DEFAULT false,  -- true if high score = low dimension
    meta JSONB,  -- Additional metadata
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(survey_id, question_num)
);

-- Answer options (for Likert scales, multiple choice)
CREATE TABLE aptitude_options (
    id BIGSERIAL PRIMARY KEY,
    question_id BIGINT REFERENCES aptitude_questions(id) ON DELETE CASCADE,
    option_num INTEGER NOT NULL,  -- 1, 2, 3, 4, 5
    label TEXT NOT NULL,  -- "전혀 아니다", "아니다", "보통이다", "그렇다", "매우 그렇다"
    value NUMERIC(3,1) NOT NULL,  -- -2.0, -1.0, 0.0, 1.0, 2.0
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student responses
CREATE TABLE aptitude_responses (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL,  -- Links to aptitude_sessions
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES aptitude_surveys(id),
    question_id BIGINT REFERENCES aptitude_questions(id),
    option_id BIGINT REFERENCES aptitude_options(id),
    raw_value NUMERIC(3,1),  -- Captured from option.value
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Survey sessions (similar to exam_sessions)
CREATE TABLE aptitude_sessions (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES aptitude_surveys(id),
    status VARCHAR(20) DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'abandoned'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_sec INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student aptitude profiles (aggregated results)
CREATE TABLE aptitude_profiles (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    
    -- Raw dimension scores (-1 to +1)
    dimension_scores JSONB NOT NULL,
    -- Example: {
    --   "STEM_interest": 0.75,
    --   "Verbal_aptitude": -0.3,
    --   "Artistic_creativity": 0.1,
    --   "Social_orientation": 0.5,
    --   "Practical_hands_on": 0.6,
    --   "Logical_reasoning": 0.8
    -- }
    
    -- Composite career/major fit scores
    career_fit_scores JSONB,
    -- Example: {
    --   "Engineering": 0.82,
    --   "Business": 0.45,
    --   "Humanities": 0.15,
    --   "Arts": 0.30,
    --   "Science": 0.78,
    --   "Medicine": 0.60
    -- }
    
    -- Top 3 recommended majors/tracks
    recommended_tracks JSONB,
    -- Example: [
    --   {"track": "Computer Science", "score": 0.92, "reason": "High STEM + Logical"},
    --   {"track": "Mechanical Engineering", "score": 0.85, "reason": "High Practical + STEM"},
    --   {"track": "Data Science", "score": 0.80, "reason": "High Logical + STEM"}
    -- ]
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT NOW(),
    based_on_survey_ids INTEGER[],  -- [1, 2, 5] (can combine multiple surveys)
    confidence_score NUMERIC(3,2),  -- 0.0-1.0 (how reliable is this profile)
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id)  -- One profile per student (updated over time)
);

-- Indexes
CREATE INDEX idx_aptitude_questions_survey ON aptitude_questions(survey_id);
CREATE INDEX idx_aptitude_questions_dimension ON aptitude_questions(dimension);
CREATE INDEX idx_aptitude_responses_student ON aptitude_responses(student_id);
CREATE INDEX idx_aptitude_responses_session ON aptitude_responses(session_id);
CREATE INDEX idx_aptitude_sessions_student ON aptitude_sessions(student_id);
CREATE INDEX idx_aptitude_profiles_student ON aptitude_profiles(student_id);
```

---

## 🔌 API Endpoints

### `/api/aptitude` Namespace

All aptitude-related endpoints under dedicated namespace.

---

### 1. Start Aptitude Survey

```http
POST /api/aptitude/surveys/{survey_id}/start
```

**Request Body:**
```json
{
  "survey_id": 1
}
```

**Success Response (201 Created):**
```json
{
  "session_id": 12345,
  "survey_id": 1,
  "survey_name": "STEM Aptitude Assessment v1",
  "total_questions": 30,
  "estimated_time_min": 15,
  "started_at": "2025-11-24T10:00:00Z"
}
```

---

### 2. Get Survey Questions

```http
GET /api/aptitude/surveys/{survey_id}/questions
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Questions per page (default: 10, max: 30)

**Success Response (200 OK):**
```json
{
  "survey_id": 1,
  "total_questions": 30,
  "page": 1,
  "per_page": 10,
  "questions": [
    {
      "question_id": 101,
      "question_num": 1,
      "question_text": "수학 문제를 푸는 것이 즐겁고 흥미롭다",
      "dimension": "STEM_interest",
      "item_type": "likert",
      "options": [
        {"option_id": 1001, "label": "전혀 아니다", "value": -2.0},
        {"option_id": 1002, "label": "아니다", "value": -1.0},
        {"option_id": 1003, "label": "보통이다", "value": 0.0},
        {"option_id": 1004, "label": "그렇다", "value": 1.0},
        {"option_id": 1005, "label": "매우 그렇다", "value": 2.0}
      ]
    },
    {
      "question_id": 102,
      "question_num": 2,
      "question_text": "글을 쓰거나 책을 읽는 것이 편하고 자연스럽다",
      "dimension": "Verbal_aptitude",
      "item_type": "likert",
      "options": [...]
    }
  ]
}
```

---

### 3. Submit Survey Responses

```http
POST /api/aptitude/surveys/{survey_id}/submit
```

**Request Body:**
```json
{
  "session_id": 12345,
  "responses": [
    {"question_id": 101, "option_id": 1004, "response_time_ms": 3200},
    {"question_id": 102, "option_id": 1003, "response_time_ms": 2800},
    {"question_id": 103, "option_id": 1005, "response_time_ms": 2500}
  ]
}
```

**Success Response (200 OK):**
```json
{
  "session_id": 12345,
  "submitted_count": 3,
  "total_questions": 30,
  "progress": 0.10,
  "message": "3 responses saved successfully"
}
```

**Complete Survey Response (if all answered):**
```json
{
  "session_id": 12345,
  "status": "completed",
  "completed_at": "2025-11-24T10:15:00Z",
  "duration_sec": 900,
  "message": "Survey completed! View your results."
}
```

---

### 4. Get Survey Results

```http
GET /api/aptitude/results/{session_id}
```

**Success Response (200 OK):**
```json
{
  "session_id": 12345,
  "student_id": 42,
  "survey_name": "STEM Aptitude Assessment v1",
  "completed_at": "2025-11-24T10:15:00Z",
  
  "dimension_scores": {
    "STEM_interest": 0.75,
    "Verbal_aptitude": -0.30,
    "Artistic_creativity": 0.10,
    "Social_orientation": 0.50,
    "Practical_hands_on": 0.60,
    "Logical_reasoning": 0.80
  },
  
  "career_fit_scores": {
    "Engineering": 0.82,
    "Computer_Science": 0.88,
    "Business": 0.45,
    "Humanities": 0.15,
    "Arts": 0.30,
    "Science": 0.78
  },
  
  "top_recommendations": [
    {
      "rank": 1,
      "major": "Computer Science / Software Engineering",
      "fit_score": 0.88,
      "reasons": [
        "높은 STEM 흥미도 (상위 15%)",
        "뛰어난 논리적 사고력 (상위 10%)",
        "실무/실습 선호도 높음"
      ],
      "related_careers": ["소프트웨어 개발자", "데이터 과학자", "AI 연구원"]
    },
    {
      "rank": 2,
      "major": "Mechanical / Electrical Engineering",
      "fit_score": 0.82,
      "reasons": [
        "높은 STEM 흥미도",
        "실무 지향적 성향",
        "문제 해결 능력 우수"
      ],
      "related_careers": ["기계 설계 엔지니어", "전자 공학 엔지니어", "로봇 공학자"]
    },
    {
      "rank": 3,
      "major": "Natural Sciences (Physics, Chemistry)",
      "fit_score": 0.78,
      "reasons": [
        "높은 논리적 사고력",
        "분석적 문제 해결 선호"
      ],
      "related_careers": ["연구원", "과학자", "교수"]
    }
  ],
  
  "feedback": {
    "summary": "당신은 **이공계 진로**에 매우 적합한 프로파일입니다. 특히 컴퓨터 과학, 소프트웨어 공학 분야에서 강점을 발휘할 것으로 예상됩니다.",
    "strengths": [
      "논리적 사고와 문제 해결 능력이 뛰어남",
      "STEM 과목에 대한 높은 흥미와 열정",
      "실습과 실무를 통한 학습 선호"
    ],
    "development_areas": [
      "언어적 표현력 향상을 위한 글쓰기 연습 권장",
      "팀 프로젝트 경험을 통한 협업 능력 개발"
    ],
    "next_steps": [
      "코딩/프로그래밍 입문 과정 수강 추천",
      "과학/수학 동아리 활동 참여",
      "이공계 선배 멘토링 프로그램 신청"
    ]
  }
}
```

---

### 5. Get Student Aptitude Profile

```http
GET /api/aptitude/profile
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "student_id": 42,
  "profile_id": 7,
  "last_updated": "2025-11-24T10:15:00Z",
  "based_on_surveys": [
    {"survey_id": 1, "name": "STEM Aptitude v1", "completed": "2025-11-20"},
    {"survey_id": 3, "name": "Learning Style v1", "completed": "2025-11-24"}
  ],
  "confidence_score": 0.85,
  
  "dimension_scores": {
    "STEM_interest": 0.75,
    "Verbal_aptitude": -0.30,
    "Artistic_creativity": 0.10,
    "Social_orientation": 0.50,
    "Practical_hands_on": 0.60,
    "Logical_reasoning": 0.80
  },
  
  "career_fit_scores": {
    "Engineering": 0.82,
    "Computer_Science": 0.88,
    "Business": 0.45,
    "Humanities": 0.15,
    "Arts": 0.30,
    "Science": 0.78
  },
  
  "recommended_tracks": [
    {"track": "Computer Science", "score": 0.88},
    {"track": "Engineering", "score": 0.82},
    {"track": "Natural Sciences", "score": 0.78}
  ],
  
  "learning_style": {
    "preferred_modality": "Visual + Hands-on",
    "study_preference": "Independent with practical application",
    "optimal_environment": "Quiet, structured, with clear goals"
  }
}
```

**If No Profile Yet (404):**
```json
{
  "detail": "No aptitude profile found. Please complete at least one survey.",
  "available_surveys": [
    {"survey_id": 1, "name": "STEM Aptitude v1"},
    {"survey_id": 2, "name": "Career Interest Inventory"}
  ]
}
```

---

## 📦 Pydantic Models

```python
# backend/app/schemas/aptitude_schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

# ─────────────────────────────────────────────────────────
# Survey Models
# ─────────────────────────────────────────────────────────

class SurveyInfo(BaseModel):
    survey_id: int
    name: str
    description: Optional[str]
    total_questions: int
    estimated_time_min: int
    active: bool

class QuestionOption(BaseModel):
    option_id: int
    label: str
    value: float

class SurveyQuestion(BaseModel):
    question_id: int
    question_num: int
    question_text: str
    dimension: str
    item_type: str
    options: List[QuestionOption]

class SurveyQuestionsResponse(BaseModel):
    survey_id: int
    total_questions: int
    page: int
    per_page: int
    questions: List[SurveyQuestion]

# ─────────────────────────────────────────────────────────
# Session Models
# ─────────────────────────────────────────────────────────

class StartSurveyRequest(BaseModel):
    survey_id: int

class StartSurveyResponse(BaseModel):
    session_id: int
    survey_id: int
    survey_name: str
    total_questions: int
    estimated_time_min: int
    started_at: datetime

class ResponseItem(BaseModel):
    question_id: int
    option_id: int
    response_time_ms: Optional[int] = None

class SubmitResponsesRequest(BaseModel):
    session_id: int
    responses: List[ResponseItem]

class SubmitResponsesResponse(BaseModel):
    session_id: int
    submitted_count: int
    total_questions: int
    progress: float
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    message: str

# ─────────────────────────────────────────────────────────
# Results Models
# ─────────────────────────────────────────────────────────

class RecommendedMajor(BaseModel):
    rank: int
    major: str
    fit_score: float
    reasons: List[str]
    related_careers: List[str]

class ResultFeedback(BaseModel):
    summary: str
    strengths: List[str]
    development_areas: List[str]
    next_steps: List[str]

class SurveyResultsResponse(BaseModel):
    session_id: int
    student_id: int
    survey_name: str
    completed_at: datetime
    dimension_scores: Dict[str, float]
    career_fit_scores: Dict[str, float]
    top_recommendations: List[RecommendedMajor]
    feedback: ResultFeedback

# ─────────────────────────────────────────────────────────
# Profile Models
# ─────────────────────────────────────────────────────────

class CompletedSurvey(BaseModel):
    survey_id: int
    name: str
    completed: str

class TrackRecommendation(BaseModel):
    track: str
    score: float

class LearningStyle(BaseModel):
    preferred_modality: str
    study_preference: str
    optimal_environment: str

class AptitudeProfileResponse(BaseModel):
    student_id: int
    profile_id: int
    last_updated: datetime
    based_on_surveys: List[CompletedSurvey]
    confidence_score: float
    dimension_scores: Dict[str, float]
    career_fit_scores: Dict[str, float]
    recommended_tracks: List[TrackRecommendation]
    learning_style: Optional[LearningStyle] = None
```

---

## 📋 Backlog: EPIC 8

### 🟪 EPIC 8 — Aptitude & Interest Assessment (Phase 2 Core)

**Priority:** High (Core Feature)  
**Estimated Effort:** 18-22 days  
**Dependencies:** Phase 1.0 Auth, Student dashboard  

---

#### **Story 8.1 — Aptitude Survey Schema & Seed Data**

**Effort:** 3 days  

**Tasks:**
- [ ] **Task 8.1.1** — Design DB schema (2 hours)
  - Create Alembic migration for 6 tables
  - Add indexes and foreign keys
  - Document dimension framework
  
- [ ] **Task 8.1.2** — Seed default survey (1 day)
  - Create "STEM Aptitude v1" with 30 questions
  - Map questions to 6 dimensions
  - Create Likert scale options (5-point)
  
- [ ] **Task 8.1.3** — Define dimension naming & scoring rules (1 day)
  - Document dimension calculation formulas
  - Create composite score algorithms
  - Define career/major mapping rules

---

#### **Story 8.2 — Aptitude API v1**

**Effort:** 5 days  

**Tasks:**
- [ ] **Task 8.2.1** — POST /api/aptitude/surveys/{id}/start (4 hours)
  - Create aptitude_sessions record
  - Return session info
  - Add student ownership check
  
- [ ] **Task 8.2.2** — GET /api/aptitude/surveys/{id}/questions (4 hours)
  - Implement pagination
  - Return questions with options
  - Order by question_num
  
- [ ] **Task 8.2.3** — POST /api/aptitude/surveys/{id}/submit (1 day)
  - Batch insert responses
  - Validate option_ids
  - Update session status on completion
  
- [ ] **Task 8.2.4** — GET /api/aptitude/results/{session_id} (2 days)
  - Calculate dimension scores (average by dimension)
  - Generate career fit scores (composite formulas)
  - Create top 3 recommendations with reasons
  - Generate feedback text (rule-based)

---

#### **Story 8.3 — Aptitude Profile Management**

**Effort:** 4 days  

**Tasks:**
- [ ] **Task 8.3.1** — Dimension score calculation service (1 day)
  - Implement scoring algorithm
  - Handle reverse-scored items
  - Normalize scores to [-1, +1] range
  
- [ ] **Task 8.3.2** — GET /api/aptitude/profile (1 day)
  - Query latest profile or aggregate from sessions
  - Return comprehensive profile
  - Calculate confidence score
  
- [ ] **Task 8.3.3** — Major/track recommendation engine (2 days)
  - Define 10-15 major categories
  - Create scoring formulas (weighted dimensions)
  - Generate reasons (template-based)
  - Map to related careers

---

#### **Story 8.4 — Frontend: Aptitude UX (Phase 2)**

**Effort:** 6 days  

**Tasks:**
- [ ] **Task 8.4.1** — Add "적성/진로 진단" menu (2 hours)
  - Update navigation
  - Create landing page
  - List available surveys
  
- [ ] **Task 8.4.2** — Likert question UI (2 days)
  - Create question card component
  - Implement 5-point Likert scale buttons
  - Add progress indicator
  - Save responses on each answer
  
- [ ] **Task 8.4.3** — Results visualization (3 days)
  - Display dimension scores (bar chart)
  - Show top 3 recommendations (cards)
  - Display feedback sections
  - Add share/download options
  
- [ ] **Task 8.4.4** — Profile dashboard (1 day)
  - Show latest profile summary
  - Display dimension radar chart (defer to Phase 2.5)
  - Link to past survey results
  - Show recommended actions

---

## 🎯 Success Criteria

After EPIC 8 completion:

1. ✅ Students can complete 30-question aptitude survey
2. ✅ System calculates 6 dimension scores accurately
3. ✅ Top 3 major/track recommendations generated
4. ✅ Profile persists and updates with new surveys
5. ✅ Frontend displays results with clear visualizations
6. ✅ Confidence score reflects profile reliability

---

## 🚀 Phase 2 Roadmap

```
Week 1-2: Story 8.1 + 8.2 (Backend schema + API)
Week 3-4: Story 8.3 (Profile engine + recommendations)
Week 5-6: Story 8.4 (Frontend UX)
Week 7: Testing & refinement
Week 8: Beta testing with 20-30 students
```

---

## 📎 Related Documents

- [PHASE1_API_CONTRACT.md](./PHASE1_API_CONTRACT.md) - Academic CAT APIs
- [PHASE2_COMBINED_INSIGHTS.md](./PHASE2_COMBINED_INSIGHTS.md) - Integration strategy (TBD)
- [DIMENSION_FRAMEWORK.md](./DIMENSION_FRAMEWORK.md) - Detailed dimension design (TBD)

---

**Status:** 📋 **READY FOR IMPLEMENTATION** (Phase 2.0)  
**Next Step:** Create seed survey with 30 sample questions  

---

**End of Aptitude Assessment Specification**
