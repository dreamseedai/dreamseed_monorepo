# Phase 1.0 - Detailed Code Analysis for API Refactoring

**Date:** November 24, 2025  
**Purpose:** Provide exact code locations and refactoring instructions for GPT-4

---

## 📁 File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routers/
│   │       ├── adaptive_exam.py       ✅ EXISTS (570 lines) - NEEDS REFACTOR
│   │       └── auth.py                ❌ MISSING - CREATE NEW
│   ├── models/
│   │   ├── user.py                    ✅ READY (User model with role, hashed_password)
│   │   ├── item.py                    ✅ READY (Item, ItemChoice, ItemPool)
│   │   └── core_entities.py           ✅ READY (ExamSession, Attempt)
│   ├── schemas/
│   │   └── exam_schemas.py            ✅ EXISTS (153 lines) - NEEDS UPDATE
│   ├── core/
│   │   ├── security.py                ⚠️ STUB (get_current_user raises 501)
│   │   ├── database.py                ✅ READY
│   │   └── services/
│   │       ├── exam_engine.py         ✅ READY (AdaptiveEngine)
│   │       ├── item_bank.py           ✅ READY (ItemBankService)
│   │       ├── adaptive_state_store.py ✅ READY (Redis state)
│   │       └── score_utils.py         ✅ READY (summarize_theta)
│   └── main.py                        ✅ READY (includes adaptive_exam_router)
```

---

## 🔍 Critical Code Locations

### 1. adaptive_exam.py - Current State

**File:** `backend/app/api/routers/adaptive_exam.py` (Line 1-570)

**Current Router Prefix:**
```python
router = APIRouter(prefix="/api/adaptive", tags=["adaptive-exam"])
```

**Current Endpoints:**
```python
@router.post("/start", response_model=StartExamResponse)
def start_adaptive_exam(...)

@router.post("/answer", response_model=SubmitAnswerResponse)
def submit_adaptive_answer(...)

@router.get("/next", response_model=NextItemResponse)
def get_next_item(
    exam_session_id: int,  # ❌ Query param (should be path param)
    ...
)

@router.get("/status", response_model=ExamStatusResponse)
def get_exam_status(
    exam_session_id: int,  # ❌ Query param (should be path param)
    ...
)
```

**Missing Endpoints:**
```python
# ❌ GET /api/adaptive/exams/{session_id}/results - DOES NOT EXIST
# ❌ GET /api/adaptive/exams/history - DOES NOT EXIST
```

---

### 2. Request/Response Models - Current State

**File:** `backend/app/api/routers/adaptive_exam.py` (Lines 113-214)

**StartExamRequest (Lines 113-115):**
```python
class StartExamRequest(BaseModel):
    exam_type: str  # placement, practice, mock, official, quiz
    class_id: Optional[int] = None
    # ❌ MISSING: pool_id (contract requires this)
```

**SubmitAnswerRequest (Lines 124-131):**
```python
class SubmitAnswerRequest(BaseModel):
    exam_session_id: int  # ❌ Should be path param, not body
    item_id: int
    correct: bool  # 🔴 SECURITY ISSUE: Frontend shouldn't provide this
    selected_choice: Optional[int] = None  # 1-5 for multiple choice
    submitted_answer: Optional[str] = None
    response_time_ms: Optional[int] = None
```

**SubmitAnswerResponse (Lines 134-140):**
```python
class SubmitAnswerResponse(BaseModel):
    attempt_id: int
    theta: float  # ❌ Contract uses new_theta
    standard_error: float  # ❌ Contract uses se
    completed: bool  # ❌ Contract uses finished
    message: str  # ❌ Contract doesn't have this field
```

**ItemChoiceResponse (Lines 143-145):**
```python
class ItemChoiceResponse(BaseModel):
    choice_num: int  # ❌ Contract uses choice_id (FK to item_choices.id)
    choice_text: str
```

**NextItemResponse (Lines 148-156):**
```python
class NextItemResponse(BaseModel):
    item_id: int
    question_text: str
    topic: Optional[str]
    choices: List[ItemChoiceResponse]
    current_theta: float  # ❌ Contract doesn't expose theta to frontend
    current_se: Optional[float]  # ❌ Contract doesn't expose SE
    attempt_count: int
    completed: bool
    # ❌ MISSING: current_item_number, estimated_remaining
```

---

### 3. Security Issue - submit_adaptive_answer()

**File:** `backend/app/api/routers/adaptive_exam.py` (Lines 315-400)

**Current Implementation (Lines 370-377):**
```python
# 🔴 SECURITY VULNERABILITY
# Load item parameters
item = db.query(Item).filter(Item.id == request.item_id).first()
if not item:
    raise HTTPException(status_code=404, detail="Item not found")

# Record attempt in engine
params = {"a": float(item.a), "b": float(item.b), "c": float(item.c)}
updated = engine.record_attempt(params, request.correct)  # ❌ Uses correct from request
```

**Problem:**
- Frontend sends `correct: bool` in request body
- Backend trusts this value without verification
- Student can cheat by always sending `correct: true`

**Required Fix:**
```python
# ✅ SECURE IMPLEMENTATION
# Load item parameters
item = db.query(Item).filter(Item.id == request.item_id).first()
if not item:
    raise HTTPException(status_code=404, detail="Item not found")

# Verify correctness from database (not request)
if request.selected_choice:  # Multiple choice
    choice = db.query(ItemChoice).filter(
        ItemChoice.item_id == item.id,
        ItemChoice.id == request.choice_id  # ❌ Need choice_id not choice_num
    ).first()
    if not choice:
        raise HTTPException(status_code=400, detail="Invalid choice_id")
    correct = bool(choice.is_correct)  # ✅ Backend determines correctness
else:  # Open-ended (future)
    # TODO: Auto-grading logic
    correct = False  # Placeholder

# Record attempt with verified correctness
params = {"a": float(item.a), "b": float(item.b), "c": float(item.c)}
updated = engine.record_attempt(params, correct)  # ✅ Use verified value
```

---

### 4. ItemChoice Model - Schema Issue

**File:** `backend/app/models/item.py` (Lines 120-139)

**Current Schema:**
```python
class ItemChoice(Base):
    __tablename__ = "item_choices"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)  # ✅ Has ID
    item_id = Column(BigInteger, ForeignKey("items.id"), nullable=False)
    choice_num = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    choice_text = Column(Text, nullable=False)
    is_correct = Column(Integer, nullable=False, default=0)  # 0 or 1
    created_at = Column(DateTime, server_default=func.now())
```

**API Response Currently Returns:**
```python
ItemChoiceResponse(
    choice_num=1,  # ❌ Not useful for submit_answer (can't link back to DB)
    choice_text="x = 3"
)
```

**API Response Should Return:**
```python
ItemChoiceResponse(
    choice_id=168,  # ✅ Primary key for submit_answer
    choice_text="x = 3"
)
```

---

### 5. Authentication Stub - security.py

**File:** `backend/app/core/security.py` (Lines 1-35)

**Current Implementation:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자 가져오기
    """
    # TODO: 실제 JWT 검증 로직 구현
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented. Please implement JWT verification."
    )
```

**Required Implementation:**
```python
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"  # ❌ Move to env var
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

---

### 6. Missing Endpoints - Skeleton Code

**Results Endpoint (TO CREATE):**
```python
@router.get("/exams/{session_id}/results", response_model=ExamResultResponse)
def get_exam_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get full exam results with feedback.
    Only available after exam is completed.
    """
    student = get_student_by_user(current_user.id, db)
    
    exam_session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.student_id == student.id
    ).first()
    
    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if exam_session.status != "completed":
        raise HTTPException(status_code=409, detail="Exam not finished yet")
    
    # Calculate results (use existing exam_session.theta, score, meta)
    # Generate feedback based on theta and accuracy
    # Return ExamResultResponse
```

**History Endpoint (TO CREATE):**
```python
@router.get("/exams/history", response_model=ExamHistoryResponse)
def get_exam_history(
    limit: int = Query(10, le=50),
    offset: int = Query(0, ge=0),
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get student's past exam sessions.
    """
    student = get_student_by_user(current_user.id, db)
    
    query = db.query(ExamSession).filter(
        ExamSession.student_id == student.id,
        ExamSession.status == "completed"
    )
    
    # Filter by subject if provided
    # Apply pagination
    # Return list of exam summaries
```

---

## 📊 Refactoring Checklist

### Phase 1A (Week 1) - Critical Path

- [ ] **Task 1: API URL Refactor** (2-3 hours)
  - [ ] Change router prefix to `/api/adaptive/exams`
  - [ ] Update endpoints: `/start`, `/{session_id}/submit-answer`, `/{session_id}/next-item`
  - [ ] Change query params to path params (`exam_session_id` → `session_id`)
  - [ ] Update tests

- [ ] **Task 2: Security Fix** (2 hours)
  - [ ] Remove `correct` from `SubmitAnswerRequest`
  - [ ] Add `choice_id` (database FK) to request
  - [ ] Implement correctness verification in backend
  - [ ] Update `ItemChoiceResponse` to return `choice_id` instead of `choice_num`

- [x] **Task 3: Auth Implementation** (4 hours)
  - [x] Install dependencies: `pip install python-jose[cryptography] passlib[bcrypt]` ✅
  - [ ] Implement JWT utilities in `security.py`
  - [ ] Create `backend/app/api/routers/auth.py`
  - [ ] Add `POST /api/auth/register`
  - [ ] Add `POST /api/auth/login`
  - [ ] Include router in `main.py`

- [ ] **Task 4: Results Endpoint** (4 hours)
  - [ ] Create `GET /api/adaptive/exams/{session_id}/results`
  - [ ] Define `ExamResultResponse` model
  - [ ] Calculate performance stats (accuracy, difficulty distribution)
  - [ ] Generate feedback (hardcoded rules based on theta)

- [ ] **Task 5: Pool Selection** (1 hour)
  - [ ] Add `pool_id: int` to `StartExamRequest`
  - [ ] Validate `pool_id` against `item_pools` table
  - [ ] Return `subject` in `StartExamResponse`

### Phase 1B (Week 2) - Polish

- [ ] **Task 6: History Endpoint** (2 hours)
  - [ ] Create `GET /api/adaptive/exams/history`
  - [ ] Implement pagination (limit, offset)
  - [ ] Filter by subject

- [ ] **Task 7: Response Model Alignment** (2 hours)
  - [ ] Rename fields: `theta` → `new_theta`, `standard_error` → `se`, `completed` → `finished`
  - [ ] Add `current_item_number`, `estimated_remaining` to `NextItemResponse`
  - [ ] Remove `current_theta`, `current_se` from frontend response

- [ ] **Task 8: Field Naming Consistency** (1 hour)
  - [ ] Standardize all fields to snake_case
  - [ ] Update OpenAPI documentation

---

## 🛠️ Required Dependencies

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

**Current requirements.txt has:**
- FastAPI ✅
- SQLAlchemy ✅
- Redis ✅
- Pydantic ✅
- Uvicorn ✅

**Need to add:**
- `python-jose` (JWT)
- `passlib` (password hashing)
- `python-multipart` (form data)

---

## 🎯 Success Criteria

After all refactoring:

1. ✅ All API URLs match contract (RESTful pattern)
2. ✅ No security vulnerabilities (correctness verified server-side)
3. ✅ JWT authentication working
4. ✅ All endpoints return contract-compliant responses
5. ✅ Frontend can use PHASE1_FRONTEND_STRUCTURE.md directly
6. ✅ Swagger UI matches contract documentation

**Ready for Week 2 Frontend Development** 🚀

---

**End of Detailed Code Analysis**
