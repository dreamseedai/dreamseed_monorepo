# Phase 1.0 Alpha - API Contract (v1)

**Project:** DreamSeed AI Platform  
**API Version:** v1.0.0  
**Date:** November 24, 2025  
**Base URL:** `https://api.dreamseedai.com` (production) or `http://localhost:8001` (dev)  
**Status:** 📋 Specification Complete  

---

## 📌 API Overview

### Authentication
All authenticated endpoints require JWT token in Authorization header:
```
Authorization: Bearer <access_token>
```

### Error Response Format
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-11-24T10:30:00Z"
}
```

### Common HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists (e.g., duplicate email)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## 🔐 Authentication Endpoints

### 1. Register (회원가입)

Creates a new user account.

```
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "name": "김철수"
}
```

**Field Validation:**
- `email` (string, required): Valid email format, unique
- `password` (string, required): Min 8 chars, must include uppercase, number, special char
- `name` (string, required): Min 2 chars, max 50 chars

**Success Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "name": "김철수",
  "role": "student",
  "created_at": "2025-11-24T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid email or password format
- `409 Conflict` - Email already exists
```json
{
  "detail": "이미 존재하는 이메일입니다",
  "code": "EMAIL_EXISTS"
}
```

---

### 2. Login (로그인)

Authenticates user and returns JWT token.

```
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "name": "김철수",
    "role": "student"
  }
}
```

**Token Details:**
- Type: JWT (JSON Web Token)
- Algorithm: HS256
- Expiration: 1 hour (3600 seconds)
- Claims: `user_id`, `email`, `role`, `exp`, `iat`

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
```json
{
  "detail": "이메일 또는 비밀번호가 잘못되었습니다",
  "code": "INVALID_CREDENTIALS"
}
```

---

### 3. Refresh Token (토큰 갱신)

**Status:** ⏸️ **DEFERRED to Phase 1B** (Not required for alpha)

```
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Note:** For alpha, users will re-login after token expiration.

---

### 4. Logout (로그아웃)

**Status:** ⏸️ **CLIENT-SIDE ONLY** (No backend endpoint needed)

Frontend should:
1. Remove token from localStorage/cookie
2. Clear user context
3. Redirect to `/login`

---

## 🧪 Adaptive Testing (CAT Engine)

### 5. Start Exam Session

Starts a new adaptive exam session.

```
POST /api/adaptive/exams/start
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "pool_id": 1
}
```

**Field Details:**
- `pool_id` (integer, required): ID of item pool
  - `1` = Math
  - `2` = English
  - `3` = Science

**Success Response (201 Created):**
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "pool_id": 1,
  "subject": "math",
  "initial_theta": 0.0,
  "created_at": "2025-11-24T10:30:00Z"
}
```

**Field Details:**
- `session_id` (uuid): Unique session identifier (use for all subsequent requests)
- `initial_theta` (float): Starting ability estimate (always 0.0)

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - Invalid pool_id
```json
{
  "detail": "Item pool not found",
  "code": "POOL_NOT_FOUND"
}
```

---

### 6. Get Next Item

Retrieves the next question in adaptive sequence.

```
GET /api/adaptive/exams/{session_id}/next-item
```

**Path Parameters:**
- `session_id` (uuid, required): Session ID from start exam

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "item_id": 42,
  "question_text": "다음 방정식을 풀어라: 2x + 5 = 13",
  "choices": [
    {
      "choice_id": 168,
      "choice_text": "x = 3"
    },
    {
      "choice_id": 169,
      "choice_text": "x = 4"
    },
    {
      "choice_id": 170,
      "choice_text": "x = 5"
    },
    {
      "choice_id": 171,
      "choice_text": "x = 6"
    }
  ],
  "current_item_number": 5,
  "estimated_remaining": 8
}
```

**Field Details:**
- `item_id` (integer): Item identifier (used for submit answer)
- `question_text` (string): Question content
- `choices` (array): 4 multiple-choice options
- `current_item_number` (integer): Progress (1-indexed)
- `estimated_remaining` (integer): Estimated items left (may change adaptively)

**Error Responses:**
- `404 Not Found` - Invalid session_id
- `410 Gone` - Exam already finished
```json
{
  "detail": "Exam session has ended",
  "code": "EXAM_FINISHED",
  "finished": true
}
```

---

### 7. Submit Answer

Submits student's answer and updates theta estimate.

```
POST /api/adaptive/exams/{session_id}/submit-answer
```

**Path Parameters:**
- `session_id` (uuid, required)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "item_id": 42,
  "choice_id": 169
}
```

**Field Details:**
- `item_id` (integer, required): Item ID from get next item
- `choice_id` (integer, required): Selected choice ID

**Success Response (200 OK):**

**Case 1: Exam continues**
```json
{
  "is_correct": true,
  "new_theta": 0.37,
  "se": 0.42,
  "finished": false,
  "items_answered": 5
}
```

**Case 2: Exam finished**
```json
{
  "is_correct": false,
  "new_theta": -0.15,
  "se": 0.28,
  "finished": true,
  "items_answered": 12,
  "termination_reason": "SE_THRESHOLD"
}
```

**Field Details:**
- `is_correct` (boolean): Whether answer was correct
- `new_theta` (float): Updated ability estimate (range: -3 to +3, typical: -2 to +2)
- `se` (float): Standard error of theta (lower = more precise)
- `finished` (boolean): **CRITICAL** - If true, no more items available, redirect to results
- `items_answered` (integer): Total items answered so far
- `termination_reason` (string, optional): Why exam ended
  - `SE_THRESHOLD` - SE < 0.3 (sufficient precision)
  - `MAX_ITEMS` - Reached maximum 20 items
  - `POOL_EXHAUSTED` - No more suitable items (rare)

**Error Responses:**
- `400 Bad Request` - Invalid item_id or choice_id
- `404 Not Found` - Session not found

---

### 8. Get Exam Status

Check current exam status (optional, for debugging).

```
GET /api/adaptive/exams/{session_id}/status
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "finished": false,
  "current_theta": 0.37,
  "current_se": 0.42,
  "items_answered": 5,
  "last_updated": "2025-11-24T10:35:00Z"
}
```

---

### 9. Get Exam Results

Retrieves final exam results (only available after finished=true).

```
GET /api/adaptive/exams/{session_id}/results
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
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
      "easy": { "attempted": 3, "correct": 3 },
      "medium": { "attempted": 7, "correct": 5 },
      "hard": { "attempted": 2, "correct": 0 }
    }
  },
  
  "feedback": {
    "summary": "중급 수준의 수학 실력을 보유하고 있습니다.",
    "strengths": ["기본 연산", "방정식"],
    "weaknesses": ["함수", "그래프"],
    "recommendation": "함수와 그래프 문제를 집중적으로 연습하면 상위 레벨로 향상 가능합니다."
  }
}
```

**Field Details:**
- `ability_estimate.theta` (float): Final ability estimate (-3 to +3 scale)
- `ability_estimate.se` (float): Standard error (should be < 0.3)
- `scores.score_0_100` (integer): Scaled score (0-100)
- `scores.level` (string): Proficiency level
  - `"Basic"` (θ < -0.5)
  - `"Intermediate"` (-0.5 ≤ θ < 0.5)
  - `"Advanced"` (θ ≥ 0.5)
- `scores.grade_letter` (string): Letter grade (A, B, C, D, F)
- `scores.grade_numeric` (integer): Korean grade scale (1-9)
- `feedback.summary` (string): 1-2 sentence overall assessment
- `feedback.recommendation` (string): Actionable next steps

**Error Responses:**
- `404 Not Found` - Session not found
- `409 Conflict` - Exam not finished yet
```json
{
  "detail": "시험이 아직 진행 중입니다",
  "code": "EXAM_NOT_FINISHED",
  "items_answered": 5,
  "finished": false
}
```

---

### 10. Get Exam History

Retrieves student's past exam sessions.

```
GET /api/adaptive/exams/history
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (integer, optional): Max results (default: 10, max: 50)
- `offset` (integer, optional): Pagination offset (default: 0)
- `subject` (string, optional): Filter by subject (`math`, `english`, `science`)

**Example:**
```
GET /api/adaptive/exams/history?limit=3&subject=math
```

**Success Response (200 OK):**
```json
{
  "total": 15,
  "limit": 3,
  "offset": 0,
  "exams": [
    {
      "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "subject": "math",
      "finished_at": "2025-11-24T10:40:00Z",
      "theta": 0.75,
      "score": 67,
      "grade": "B",
      "level": "Intermediate",
      "items_answered": 12
    },
    {
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "subject": "math",
      "finished_at": "2025-11-20T14:20:00Z",
      "theta": 0.35,
      "score": 58,
      "grade": "C",
      "level": "Intermediate",
      "items_answered": 15
    },
    {
      "session_id": "12345678-90ab-cdef-1234-567890abcdef",
      "subject": "math",
      "finished_at": "2025-11-15T09:10:00Z",
      "theta": -0.10,
      "score": 48,
      "grade": "D",
      "level": "Basic",
      "items_answered": 18
    }
  ]
}
```

**Field Details:**
- `total` (integer): Total number of exams (all pages)
- `exams` (array): Exam summary objects (sorted by finished_at DESC)

**Error Responses:**
- `401 Unauthorized` - Not authenticated

---

## 🔍 Item Pools (Reference)

### Get Available Pools

**Status:** ⏸️ **OPTIONAL for Alpha** (hardcode in frontend)

```
GET /api/adaptive/pools
```

**Success Response (200 OK):**
```json
{
  "pools": [
    {
      "pool_id": 1,
      "name": "Math",
      "subject": "math",
      "description": "수학 진단 테스트",
      "total_items": 40,
      "difficulty_range": [-2.5, 2.5],
      "enabled": true
    },
    {
      "pool_id": 2,
      "name": "English",
      "subject": "english",
      "description": "영어 진단 테스트 (준비 중)",
      "total_items": 40,
      "difficulty_range": [-2.5, 2.5],
      "enabled": false
    },
    {
      "pool_id": 3,
      "name": "Science",
      "subject": "science",
      "description": "과학 진단 테스트 (준비 중)",
      "total_items": 40,
      "difficulty_range": [-2.5, 2.5],
      "enabled": false
    }
  ]
}
```

---

## 🏥 Health Check

### Health Status

```
GET /health
```

**Success Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-24T10:30:00Z",
  "services": {
    "database": "up",
    "redis": "up"
  }
}
```

---

## 📊 API Summary Table

| Endpoint | Method | Auth | Status | Phase |
|----------|--------|------|--------|-------|
| `/api/auth/register` | POST | ❌ | ❌ To Implement | Week 1 |
| `/api/auth/login` | POST | ❌ | ❌ To Implement | Week 1 |
| `/api/auth/refresh` | POST | ✅ | ⏸️ Deferred | Phase 1B |
| `/api/adaptive/exams/start` | POST | ✅ | ✅ Ready | Phase 0.5 |
| `/api/adaptive/exams/{id}/next-item` | GET | ✅ | ✅ Ready | Phase 0.5 |
| `/api/adaptive/exams/{id}/submit-answer` | POST | ✅ | ✅ Ready | Phase 0.5 |
| `/api/adaptive/exams/{id}/status` | GET | ✅ | ✅ Ready | Phase 0.5 |
| `/api/adaptive/exams/{id}/results` | GET | ✅ | ✅ Ready | Phase 0.5 |
| `/api/adaptive/exams/history` | GET | ✅ | ❌ To Implement | Week 1 |
| `/api/adaptive/pools` | GET | ❌ | ⏸️ Optional | Phase 1B |
| `/health` | GET | ❌ | ✅ Ready | Phase 0.5 |

**Legend:**
- ✅ Ready: Implemented and tested
- ❌ To Implement: Required for alpha, not yet implemented
- ⏸️ Deferred: Nice-to-have, defer to later phase

---

## 🚨 Known Limitations (Alpha)

### 1. No Refresh Token
- Access tokens expire after 1 hour
- User must re-login (no seamless refresh)
- **Mitigation:** Phase 1B will add refresh token flow

### 2. No Password Reset
- Users cannot reset forgotten passwords
- **Workaround:** Manual support or admin reset
- **Mitigation:** Phase 1B will add email-based reset

### 3. No Pagination Cursor
- History endpoint uses offset-based pagination
- Can skip results if new exams added during pagination
- **Mitigation:** Phase 2 will add cursor-based pagination

### 4. No Rate Limiting
- APIs have no rate limits (vulnerable to abuse)
- **Mitigation:** Phase 1B will add per-user rate limits

### 5. No Partial Results
- If exam interrupted (browser close), no partial results saved
- User must restart exam
- **Mitigation:** Phase 2 will add resume capability

---

## 🔄 API Versioning Strategy

**Current:** v1.0.0 (implicit, no version in URL)

**Future Versions:**
- v1.1.0: Add refresh token, password reset (Phase 1B)
- v1.2.0: Add multi-subject comparison (Phase 2)
- v2.0.0: Breaking changes (if needed)

**URL Strategy (Phase 2):**
```
/api/v1/adaptive/exams/start  (explicit version)
/api/v2/adaptive/exams/start  (future)
```

---

## 📖 OpenAPI / Swagger

**Interactive API Docs:**
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`
- OpenAPI JSON: `http://localhost:8001/openapi.json`

**Note:** These are auto-generated by FastAPI and will be available once auth endpoints are implemented.

---

## 🧪 Example API Flow (Full Exam)

### 1. Register & Login
```bash
# Register
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!","name":"테스트"}'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
# Save access_token from response
```

### 2. Start Exam
```bash
curl -X POST http://localhost:8001/api/adaptive/exams/start \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"pool_id":1}'
# Save session_id from response
```

### 3. Get First Item
```bash
curl -X GET http://localhost:8001/api/adaptive/exams/<session_id>/next-item \
  -H "Authorization: Bearer <access_token>"
# Save item_id and choice_id
```

### 4. Submit Answer (repeat until finished=true)
```bash
curl -X POST http://localhost:8001/api/adaptive/exams/<session_id>/submit-answer \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"item_id":42,"choice_id":169}'
# Check finished field in response
```

### 5. Get Results
```bash
curl -X GET http://localhost:8001/api/adaptive/exams/<session_id>/results \
  -H "Authorization: Bearer <access_token>"
```

### 6. Get History
```bash
curl -X GET http://localhost:8001/api/adaptive/exams/history \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚠️ Conflicts with Existing Code

### 🔴 CONFLICT DETECTED

**File:** `backend/app/api/routers/adaptive.py`

**Issue:** Existing endpoints may have different request/response formats than this contract.

**Current Implementation (Phase 0.5):**
- `/api/adaptive/exams/start` - EXISTS but may need pool_id parameter added
- `/api/adaptive/exams/{id}/next-item` - EXISTS
- `/api/adaptive/exams/{id}/submit-answer` - EXISTS but may return different fields
- `/api/adaptive/exams/{id}/results` - EXISTS but response format may differ

**Action Required:**
1. Review `backend/app/api/routers/adaptive.py`
2. Compare actual response format with this contract
3. Update either the contract or the implementation to match
4. Add missing fields (e.g., `feedback.recommendation` in results)

**GPT Task:**
> "Review backend/app/api/routers/adaptive.py and compare with PHASE1_API_CONTRACT.md. 
> List all differences in request/response formats. 
> Provide migration plan to align implementation with contract."

---

**Status:** 📋 **CONTRACT COMPLETE - REQUIRES IMPLEMENTATION REVIEW**  
**Next Step:** Validate against existing Phase 0.5 code  
**Related Docs:**
- [PHASE1_TASK_BREAKDOWN.md](./PHASE1_TASK_BREAKDOWN.md)
- [PHASE1_FRONTEND_STRUCTURE.md](./PHASE1_FRONTEND_STRUCTURE.md)

---

## 🔮 Future APIs (Phase 2+)

### Aptitude & Interest Assessment

**Status:** ⏸️ **Planned for Phase 2.0**

DreamSeed AI's second core pillar: **Student aptitude/interest profiling** for career/major guidance.

**Namespace:** `/api/aptitude`

**Planned Endpoints:**
- `POST /api/aptitude/surveys/{survey_id}/start` - Start aptitude survey
- `GET /api/aptitude/surveys/{survey_id}/questions` - Get survey questions
- `POST /api/aptitude/surveys/{survey_id}/submit` - Submit responses
- `GET /api/aptitude/results/{session_id}` - Get survey results with recommendations
- `GET /api/aptitude/profile` - Get student's aptitude profile

**Dimensions:**
- STEM_interest, Verbal_aptitude, Artistic_creativity
- Social_orientation, Practical_hands_on, Logical_reasoning

**Output:**
- Career/major fit scores (Engineering, Business, Humanities, Arts, etc.)
- Top 3 recommended majors with reasons
- Learning style preferences
- Personalized next steps

**Full Specification:** See [PHASE2_APTITUDE_ASSESSMENT.md](../phase2/PHASE2_APTITUDE_ASSESSMENT.md)

---

**End of API Contract v1.0.0**
