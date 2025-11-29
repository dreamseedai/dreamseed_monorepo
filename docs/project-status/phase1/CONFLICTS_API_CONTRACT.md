# API Contract Conflicts Analysis

**Date:** November 24, 2025  
**Status:** ⚠️ **CONFLICTS DETECTED** (Based on Actual Code Review)  
**Impact:** Moderate - Requires backend endpoint adjustments before frontend development

**Files Analyzed:**
- `backend/app/api/routers/adaptive_exam.py` (570 lines)
- `backend/app/schemas/exam_schemas.py` (153 lines)
- `backend/app/models/core_entities.py` (ExamSession, Attempt)
- `backend/app/models/item.py` (Item, ItemChoice, ItemPool)
- `backend/app/core/security.py` (get_current_user - NOT IMPLEMENTED)

---

## 🔴 Critical Conflicts (Must Resolve Before Phase 1)

### 1. API URL Pattern Mismatch

**Contract (PHASE1_API_CONTRACT.md):**
```
POST /api/adaptive/exams/start
GET  /api/adaptive/exams/{session_id}/next-item
POST /api/adaptive/exams/{session_id}/submit-answer
GET  /api/adaptive/exams/{session_id}/results
GET  /api/adaptive/exams/{session_id}/status
GET  /api/adaptive/exams/history
```

**Existing Code (backend/app/api/routers/adaptive_exam.py):**
```python
POST /api/adaptive/start
POST /api/adaptive/answer
GET  /api/adaptive/next
GET  /api/adaptive/status
```

**Differences:**
- ❌ Contract uses `/exams/` prefix (RESTful collection pattern)
- ❌ Existing code uses flat structure (`/start`, `/answer`, `/next`)
- ❌ Contract uses `{session_id}` path parameter (e.g., `/exams/123/next-item`)
- ❌ Existing code uses `exam_session_id` query parameter (e.g., `/next?exam_session_id=123`)
- ❌ Contract has `/results` endpoint (not implemented)
- ❌ Contract has `/history` endpoint (not implemented)

**Recommendation:**
**Option A: Update Backend to Match Contract (Preferred)**
- Rationale: RESTful `/exams/{id}/action` pattern is industry standard
- Impact: Requires router changes but improves API design
- Effort: 2-3 hours to refactor and test

**Option B: Update Contract to Match Backend**
- Rationale: Minimizes backend changes
- Impact: Frontend uses less intuitive query params
- Effort: 1 hour documentation update

**GPT Task:**
> "Refactor backend/app/api/routers/adaptive_exam.py to use RESTful URL pattern:
> - Change prefix to `/api/adaptive/exams`
> - Use `{session_id}` path parameter instead of query param
> - Rename endpoints: `/start` → `/start`, `/answer` → `/{session_id}/submit-answer`, `/next` → `/{session_id}/next-item`
> - Add missing `/api/adaptive/exams/{session_id}/results` endpoint
> - Add missing `/api/adaptive/exams/history` endpoint
> - Update all request/response models to match PHASE1_API_CONTRACT.md"

---

### 2. Request/Response Model Differences

#### 2.1 Start Exam Endpoint

**Contract:**
```json
// Request
{
  "pool_id": 1  // Required: 1=Math, 2=English, 3=Science
}

// Response
{
  "session_id": "uuid",
  "pool_id": 1,
  "subject": "math",
  "initial_theta": 0.0,
  "created_at": "2025-11-24T10:30:00Z"
}
```

**Existing Code:**
```python
# Request
class StartExamRequest(BaseModel):
    exam_type: str  # placement, practice, mock, official, quiz
    class_id: Optional[int] = None

# Response
class StartExamResponse(BaseModel):
    exam_session_id: int
    message: str
    initial_theta: float
```

**Differences:**
- ❌ Contract uses `pool_id` (item pool selection)
- ❌ Existing code uses `exam_type` (placement/practice/mock)
- ❌ Contract returns `subject` name (math/english/science)
- ❌ Existing code returns `message` field (not in contract)
- ❌ Contract uses UUID for session_id (existing uses int)
- ❌ Contract returns `created_at` timestamp (not in existing)

**Recommendation:**
Keep `exam_type` in backend (DB requirement) but add `pool_id` as parameter:
```python
class StartExamRequest(BaseModel):
    pool_id: int  # 1=Math, 2=English, 3=Science
    exam_type: str = "practice"  # Default to practice
    class_id: Optional[int] = None

class StartExamResponse(BaseModel):
    session_id: str  # Change from exam_session_id to session_id (keep int or uuid)
    pool_id: int
    subject: str  # Derived from pool_id (1→"math", 2→"english", 3→"science")
    initial_theta: float
    created_at: datetime
```

---

#### 2.2 Submit Answer Endpoint

**Contract:**
```json
// Request
{
  "item_id": 42,
  "choice_id": 169  // Selected choice ID
}

// Response
{
  "is_correct": true,
  "new_theta": 0.37,
  "se": 0.42,
  "finished": false,
  "items_answered": 5,
  "termination_reason": "SE_THRESHOLD"  // Optional
}
```

**Existing Code:**
```python
# Request
class SubmitAnswerRequest(BaseModel):
    exam_session_id: int  # In request body (contract uses path param)
    item_id: int
    correct: bool  # Frontend shouldn't know correctness!
    selected_choice: Optional[int] = None  # 1-5 (contract uses choice_id)
    submitted_answer: Optional[str] = None
    response_time_ms: Optional[int] = None

# Response
class SubmitAnswerResponse(BaseModel):
    attempt_id: int
    theta: float
    standard_error: float
    completed: bool
    message: str
```

**Differences:**
- 🔴 **CRITICAL:** Existing request requires `correct: bool` field
  - Security issue: Frontend shouldn't determine correctness
  - Backend should calculate correctness from `item_id` + `choice_id`
- ❌ Contract uses `choice_id` (database foreign key)
- ❌ Existing uses `selected_choice` (1-5 index)
- ❌ Contract has `termination_reason` in response
- ❌ Contract returns `items_answered` count

**Recommendation:**
```python
class SubmitAnswerRequest(BaseModel):
    item_id: int
    choice_id: int  # Change from selected_choice (use DB FK)
    response_time_ms: Optional[int] = None
    # Remove: correct (backend calculates), exam_session_id (in URL path)

class SubmitAnswerResponse(BaseModel):
    is_correct: bool  # Add this field
    new_theta: float  # Rename from theta
    se: float  # Rename from standard_error
    finished: bool  # Rename from completed
    items_answered: int  # Add this field
    termination_reason: Optional[str] = None  # Add SE_THRESHOLD, MAX_ITEMS, POOL_EXHAUSTED
```

**GPT Task:**
> "Security fix: Remove `correct` field from SubmitAnswerRequest. 
> Backend must calculate correctness by:
> 1. Load ItemChoice.is_correct for given choice_id
> 2. Set correct = choice.is_correct
> 3. Never trust frontend to provide correct field"

---

#### 2.3 Get Next Item Endpoint

**Contract:**
```json
// Response
{
  "item_id": 42,
  "question_text": "다음 방정식을 풀어라: 2x + 5 = 13",
  "choices": [
    {"choice_id": 168, "choice_text": "x = 3"},
    {"choice_id": 169, "choice_text": "x = 4"}
  ],
  "current_item_number": 5,
  "estimated_remaining": 8
}
```

**Existing Code:**
```python
class ItemChoiceResponse(BaseModel):
    choice_num: int  # 1-5 index
    choice_text: str

class NextItemResponse(BaseModel):
    item_id: int
    question_text: str
    topic: Optional[str]
    choices: List[ItemChoiceResponse]
    current_theta: float
    current_se: Optional[float]
    attempt_count: int
    completed: bool
```

**Differences:**
- ❌ Contract uses `choice_id` (database ID for submit-answer)
- ❌ Existing uses `choice_num` (1-5 index, not linkable to DB)
- ❌ Contract has `current_item_number` and `estimated_remaining` (progress tracking)
- ❌ Existing has `current_theta` and `current_se` (not in contract - security/UX issue?)

**Recommendation:**
```python
class ItemChoiceResponse(BaseModel):
    choice_id: int  # Change from choice_num (use DB FK)
    choice_text: str
    # DO NOT EXPOSE: is_correct (security issue)

class NextItemResponse(BaseModel):
    item_id: int
    question_text: str
    choices: List[ItemChoiceResponse]
    current_item_number: int  # Add progress tracking
    estimated_remaining: int  # Add estimated items left
    # Remove: current_theta, current_se (internal metrics, not user-facing)
    # Remove: completed (handled by HTTP 410 Gone or finished flag in submit)
```

---

#### 2.4 Get Results Endpoint (Missing)

**Contract:**
```json
GET /api/adaptive/exams/{session_id}/results

// Response
{
  "session_id": "uuid",
  "subject": "math",
  "finished_at": "2025-11-24T10:40:00Z",
  
  "ability_estimate": {
    "theta": 0.75,
    "se": 0.28,
    "confidence_interval": [-0.30, 1.80]
  },
  
  "scores": {
    "score_0_100": 67,
    "t_score": 58,
    "percentile": 70,
    "grade_letter": "B",
    "grade_numeric": 6,
    "level": "Intermediate"
  },
  
  "performance": {
    "total_items": 12,
    "correct_items": 8,
    "accuracy": 0.67,
    "difficulty_distribution": {
      "easy": {"attempted": 3, "correct": 3},
      "medium": {"attempted": 7, "correct": 5},
      "hard": {"attempted": 2, "correct": 0}
    }
  },
  
  "feedback": {
    "summary": "중급 수준의 수학 실력을 보유하고 있습니다.",
    "strengths": ["기본 연산", "방정식"],
    "weaknesses": ["함수", "그래프"],
    "recommendation": "함수와 그래프 문제를 집중적으로 연습하면..."
  }
}
```

**Existing Code:**
```python
# ENDPOINT DOES NOT EXIST
# GET /api/adaptive/status returns minimal info
```

**Status:** ❌ **NOT IMPLEMENTED**

**Recommendation:**
Create new endpoint `/api/adaptive/exams/{session_id}/results`:
- Query ExamSession + Attempts for stats
- Use existing `summarize_theta()` from `score_utils.py`
- Add difficulty distribution calculation
- Generate feedback text (hardcoded rules or GPT-4 in Phase 2)

**GPT Task:**
> "Implement GET /api/adaptive/exams/{session_id}/results endpoint:
> 1. Verify exam_session.status == 'completed'
> 2. Calculate ability_estimate (theta, se, CI)
> 3. Calculate scores using score_utils.summarize_theta()
> 4. Calculate performance stats (total_items, correct_items, accuracy)
> 5. Calculate difficulty_distribution (easy/medium/hard breakdown)
> 6. Generate feedback (hardcoded rules based on theta and accuracy)
> 7. Return ExamResultResponse matching contract"

---

#### 2.5 Get History Endpoint (Missing)

**Contract:**
```json
GET /api/adaptive/exams/history?limit=3&subject=math

// Response
{
  "total": 15,
  "limit": 3,
  "offset": 0,
  "exams": [
    {
      "session_id": "uuid",
      "subject": "math",
      "finished_at": "2025-11-24T10:40:00Z",
      "theta": 0.75,
      "score": 67,
      "grade": "B",
      "level": "Intermediate",
      "items_answered": 12
    }
  ]
}
```

**Existing Code:**
```python
# ENDPOINT DOES NOT EXIST
```

**Status:** ❌ **NOT IMPLEMENTED**

**Recommendation:**
Create new endpoint `/api/adaptive/exams/history`:
- Query ExamSession WHERE student_id = current_user.student_id AND status = 'completed'
- Filter by subject if provided
- Paginate with limit/offset
- Return summary list (no full details)

**GPT Task:**
> "Implement GET /api/adaptive/exams/history endpoint:
> 1. Get current_user.student_id
> 2. Query ExamSession WHERE student_id=X AND status='completed'
> 3. Filter by subject if provided (query param)
> 4. Apply pagination (limit, offset)
> 5. Return ExamHistoryResponse with total count and exam summaries"

---

## 🟡 Moderate Conflicts (Address in Week 1-2)

### 3. Authentication Endpoints (Missing)

**Contract:**
```
POST /api/auth/register
POST /api/auth/login
```

**Existing Code Analysis:**

✅ **User Model** (`backend/app/models/user.py`):
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # student, parent, teacher, tutor, admin
    is_active = Column(Boolean, default=True)
    created_at, updated_at = ...
```
**Status:** ✅ Ready for auth implementation

❌ **Security Utilities** (`backend/app/core/security.py`):
```python
def get_current_user(...) -> User:
    # TODO: 실제 JWT 검증 로직 구현
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented. Please implement JWT verification."
    )
```
### 4. Pool/Subject Mapping (Data Model Analysis)

**Contract Assumption:**
- `pool_id` directly maps to subject: 1=Math, 2=English, 3=Science
- Items belong to one pool

**Existing Code Analysis:**

✅ **ItemPool Model** (`backend/app/models/item.py`):
```python
class ItemPool(Base):
    __tablename__ = "item_pools"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True, index=True)  # ✅ SUBJECT FIELD EXISTS
    grade_level = Column(String(20), nullable=True)
    meta = Column(JSON, nullable=True)
    created_at, updated_at = ...
    
    # Many-to-many with Items via item_pool_membership
    items = relationship("Item", secondary="item_pool_membership", backref="pools")
```
**Status:** ✅ Model already exists!

✅ **Item-Pool Junction Table:**
```python
class ItemPoolMembership(Base):
    __tablename__ = "item_pool_membership"
    item_id = Column(BigInteger, ForeignKey("items.id"), primary_key=True)
    pool_id = Column(Integer, ForeignKey("item_pools.id"), primary_key=True)
    sequence = Column(Integer, nullable=True)
    weight = Column(Numeric(5, 2), default=1.0)
```
**Status:** ✅ Many-to-many relationship supported

❌ **Start Exam Endpoint Issue:**
```python
class StartExamRequest(BaseModel):
    exam_type: str  # ❌ No pool_id parameter
    class_id: Optional[int] = None
```
**Problem:** Request model doesn't accept `pool_id`, so frontend can't specify Math/English/Science

**Recommendation:**
```python
class StartExamRequest(BaseModel):
    pool_id: int  # ADD THIS
    exam_type: str = "practice"  # Make optional with default
    class_id: Optional[int] = None
```pp/api/routers/auth.py:
> 1. POST /api/auth/register (validate email, hash password with bcrypt, create User)
> 2. POST /api/auth/login (verify email/password, generate JWT with 1hr expiration)
> 3. Use existing User model and security.py
> 4. Include router in main.py"

---

### 4. Pool/Subject Mapping (Data Model Mismatch)

**Contract Assumption:**
- `pool_id` directly maps to subject: 1=Math, 2=English, 3=Science
- Items belong to one pool

**Existing Code:**
- `Item` table has `pool_id` (integer) and `subject` (string)
- Seed data created 3 pools (Math, English, Science)

**Issue:**
- No `Pool` table definition found
- No validation that `pool_id = 1` means "math"

**Recommendation:**
Week 1 Task:
1. Create `Pool` model (id, name, subject, enabled)
2. Seed 3 pools with proper mapping
3. Add validation in start exam endpoint

**GPT Task:**
> "Create backend/app/models/pool.py:
> 1. Define Pool model (id, name, subject, description, enabled)
> 2. Create Alembic migration to add pools table
> 3. Seed 3 pools in migration: (1, 'Math', 'math', true), (2, 'English', 'english', false), (3, 'Science', 'science', false)
> 4. Update start exam endpoint to validate pool_id against Pool table"

---

## 🟢 Minor Conflicts (Can Defer to Phase 1B)

### 5. UUID vs Integer for Session ID

**Contract:** Uses `session_id` as UUID string  
**Existing Code:** Uses `exam_session_id` as integer

**Recommendation:**
Keep integer for Phase 1.0 (simpler, faster lookups). Change contract to match:
```diff
- "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
+ "session_id": 123
```

**Rationale:** UUID adds complexity without benefits for 5-10 alpha users.

---

### 6. Field Naming Consistency

**Contract:** Uses snake_case consistently (score_0_100, items_answered)  
**Existing Code:** Uses mixed patterns (exam_session_id, attempt_count)

**Recommendation:**
Week 2 Task: Standardize all response models to snake_case to match contract.

---

## 📋 Summary Table

| Issue | Severity | Status | Effort | Week |
|-------|----------|--------|--------|------|
| API URL Pattern Mismatch | 🔴 Critical | Not Fixed | 2-3 hours | Week 1 |
| Start Exam Request/Response | 🔴 Critical | Not Fixed | 1 hour | Week 1 |
| Submit Answer Security Issue | 🔴 Critical | Not Fixed | 2 hours | Week 1 |
| Get Next Item Response | 🟡 Moderate | Not Fixed | 1 hour | Week 1 |
| Get Results Endpoint Missing | 🔴 Critical | Not Impl | 4 hours | Week 1 |
| Get History Endpoint Missing | 🟡 Moderate | Not Impl | 2 hours | Week 2 |
| Auth Endpoints Missing | 🔴 Critical | Not Impl | 4 hours | Week 1 |
| Pool Table Missing | 🟡 Moderate | Not Impl | 1 hour | Week 1 |
| UUID vs Integer | 🟢 Minor | Contract Update | 10 min | Week 1 |
| Field Naming Consistency | 🟢 Minor | Not Fixed | 1 hour | Week 2 |

**Total Effort:** ~19 hours backend work (Week 1-2)

---

## 🚀 Implementation Priority

### Week 1 (Must Have - P0)

1. **API URL Refactor** (2-3 hours)
   - Change `/api/adaptive/` to `/api/adaptive/exams/`
   - Use path params `{session_id}` instead of query params

2. **Security Fix: Submit Answer** (2 hours)
   - Remove `correct` field from request
   - Backend calculates correctness from `choice_id`

3. **Auth Endpoints** (4 hours)
   - POST `/api/auth/register`
   - POST `/api/auth/login`

4. **Results Endpoint** (4 hours)
   - GET `/api/adaptive/exams/{session_id}/results`
   - Full response with scores, performance, feedback

5. **Pool Table** (1 hour)
   - Create Pool model
   - Alembic migration
   - Seed 3 pools

**Week 1 Total:** 13-14 hours

### Week 2 (Should Have - P1)

6. **History Endpoint** (2 hours)
   - GET `/api/adaptive/exams/history`

7. **Response Model Alignment** (2 hours)
   - Update all response fields to match contract
   - Add `current_item_number`, `estimated_remaining`

8. **Field Naming Standardization** (1 hour)
   - Consistent snake_case across all APIs

**Week 2 Total:** 5 hours

---

---

## 🎯 VERIFIED CONFLICT SUMMARY

Based on actual code review of `backend/app/api/routers/adaptive_exam.py`:

| Issue | Current State | Contract Requirement | Priority |
|-------|--------------|---------------------|----------|
| **URL Pattern** | `/api/adaptive/start`, `/answer`, `/next` | `/api/adaptive/exams/start`, `/{id}/submit-answer` | 🔴 P0 |
| **Security: correct field** | `SubmitAnswerRequest.correct: bool` (frontend provides) | Backend calculates from `choice_id` | 🔴 P0 |
| **Response Fields** | `theta`, `standard_error`, `completed` | `new_theta`, `se`, `finished` | 🟡 P1 |
| **Auth Endpoint** | `get_current_user()` raises 501 | JWT verification working | 🔴 P0 |
| **Results Endpoint** | Does not exist | `GET /exams/{id}/results` with full feedback | 🔴 P0 |
| **History Endpoint** | Does not exist | `GET /exams/history` with pagination | 🟡 P1 |
| **Pool Selection** | `StartExamRequest` has no `pool_id` | `pool_id: int` required | 🔴 P0 |

**Total P0 Issues:** 5 (13-14 hours)  
**Total P1 Issues:** 2 (5 hours)  

---

## ✅ Action Items for GPT

Copy these tasks to GPT-4 for implementation:

### Task 1: API URL Refactor
```
Refactor backend/app/api/routers/adaptive_exam.py:
1. Change router prefix to /api/adaptive/exams
2. Update endpoints:
   - POST /start → POST /start (no change)
   - POST /answer → POST /{session_id}/submit-answer
   - GET /next → GET /{session_id}/next-item
   - GET /status → GET /{session_id}/status (no change)
3. Change exam_session_id from query param to path param in all endpoints
4. Update all function signatures
5. Update tests in backend/tests/test_adaptive_exam_e2e.py
```

### Task 2: Security Fix
```
Fix SubmitAnswerRequest in backend/app/api/routers/adaptive_exam.py:
1. Remove correct: bool field from SubmitAnswerRequest
2. Change selected_choice to choice_id: int
3. In submit_adaptive_answer():
   - Load ItemChoice by choice_id
   - Set correct = choice.is_correct
   - Pass correct to engine.record_attempt()
4. Update response model to match contract (is_correct, new_theta, se, finished)
```

### Task 3: Auth Endpoints
```
Create backend/app/api/routers/auth.py:
1. POST /api/auth/register:
   - Validate email format, password strength (min 8 chars, uppercase, number, special)
   - Check email uniqueness
   - Hash password with bcrypt
   - Create User with role="student"
   - Return user info (no password)
2. POST /api/auth/login:
   - Verify email/password
   - Generate JWT with 1hr expiration (HS256)
   - Claims: user_id, email, role, exp, iat
   - Return access_token + user info
3. Include router in backend/main.py
4. Write tests for both endpoints
```

### Task 4: Results Endpoint
```
Add GET /api/adaptive/exams/{session_id}/results to backend/app/api/routers/adaptive_exam.py:
1. Verify exam_session.status == 'completed' (409 if not)
2. Calculate ability_estimate (theta, se, CI = [theta - 1.96*se, theta + 1.96*se])
3. Use score_utils.summarize_theta() for scores
4. Calculate performance:
   - Query Attempt.count() for total_items, correct_items
   - accuracy = correct_items / total_items
   - difficulty_distribution: join Attempt + Item, group by difficulty range
5. Generate feedback (hardcoded rules):
   - summary based on theta range
   - strengths/weaknesses based on topic accuracy
   - recommendation based on level
6. Return ExamResultResponse matching PHASE1_API_CONTRACT.md
```

### Task 5: History Endpoint
```
Add GET /api/adaptive/exams/history to backend/app/api/routers/adaptive_exam.py:
1. Query ExamSession WHERE student_id = current_user.student_id AND status = 'completed'
2. Filter by subject if query param provided
3. Paginate with limit (default 10, max 50) and offset (default 0)
4. For each exam, include: session_id, subject, finished_at, theta, score, grade, level, items_answered
5. Return ExamHistoryResponse with total count and exam list
6. Sort by finished_at DESC
```

### Task 6: Pool Table
```
Create backend/app/models/pool.py and Alembic migration:
1. Define Pool model:
   - id (int, PK)
   - name (str, 50)
   - subject (str, 20, index)
   - description (str, 200)
   - enabled (bool, default True)
   - created_at (datetime)
2. Create migration backend/alembic/versions/004_pools.py
3. Seed 3 pools in migration:
   INSERT INTO pools VALUES (1, 'Math', 'math', '수학 진단 테스트', true, NOW())
   INSERT INTO pools VALUES (2, 'English', 'english', '영어 진단 테스트 (준비 중)', false, NOW())
   INSERT INTO pools VALUES (3, 'Science', 'science', '과학 진단 테스트 (준비 중)', false, NOW())
4. Update start_adaptive_exam() to validate pool_id against Pool table
5. Return pool.subject in StartExamResponse
```

---

## 🎯 Expected Outcome

After all conflicts resolved (Week 1-2):

✅ API URLs match contract (RESTful `/exams/{id}/action` pattern)  
✅ Request/response models align with contract  
✅ Security fixed (no `correct` field from frontend)  
✅ Auth endpoints implemented (register, login)  
✅ Results endpoint with full feedback  
✅ History endpoint with pagination  
✅ Pool table with subject mapping  
✅ Frontend can use PHASE1_FRONTEND_STRUCTURE.md directly  

**Status:** Ready for Week 2 Frontend Development 🚀

---

**End of Conflicts Analysis**
