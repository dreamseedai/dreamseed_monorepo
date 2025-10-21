#!/usr/bin/env bash
set -euo pipefail

# ============================
# 커스텀 파라미터(필요 시 수정)
# ============================
BRANCH_NAME="${BRANCH_NAME:-feat/seedtest-api-scaffold}"
PR_TITLE="${PR_TITLE:-PR-SeedTest-API Scaffold (FastAPI + OpenAPI)}"
PR_BODY="${PR_BODY:-SeedTest Exam API scaffold:
- FastAPI + OpenAPI (/docs)
- JWT(JWKS) 의존성/LOCAL_DEV fallback
- Endpoints: POST /api/seedtest/exams, GET /api/seedtest/exams/{session_id}/next, POST /api/seedtest/exams/{session_id}/response, GET /api/seedtest/exams/{session_id}/result
- Adaptive engine stub
- Correlation-ID middleware

다음 단계:
- JWT RS256 운영값 주입(JWKS_URL/JWT_ISS/JWT_AUD)
- 멀티테넌시(org 교차검증), Idempotency 처리, 타임아웃/완료(reason: timeout)
- Adaptive Engine ↔ DB/IRT 통합
}"
REVIEWERS="${REVIEWERS:-}"   # 예: "platform-admin,sre-lead,security-lead"

# 베이스 디렉토리(원하면 수정)
BASE="${BASE:-apps/seedtest-api}"

# ============================
# 사전 점검
# ============================
if ! command -v git >/dev/null 2>&1; then
  echo "❌ git not found"; exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ gh CLI not found (https://cli.github.com/)"; exit 1
fi
gh auth status >/dev/null || { echo "❌ gh auth login 먼저 수행하세요"; exit 1; }

# 워킹트리 확인(선택)
if [ -n "$(git status --porcelain)" ]; then
  echo "ℹ️ 워킹트리에 변경이 있습니다. 계속 진행합니다(추가 변경도 함께 커밋됩니다)."
fi

# 브랜치 생성
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
  git checkout "$BRANCH_NAME"
else
  git checkout -b "$BRANCH_NAME"
fi

# 디렉토리 생성
mkdir -p "$BASE"/{schemas,routers,services,security,middleware}
mkdir -p scripts

# ============================
# 파일 생성(존재 시 덮어쓰기 X)
# ============================

# requirements.txt
REQ="$BASE/requirements.txt"
if [ ! -f "$REQ" ]; then
cat > "$REQ" <<'PY'
fastapi==0.114.0
uvicorn[standard]==0.30.6
pydantic==2.8.2
python-jose==3.3.0
httpx==0.27.2
PY
fi

# settings.py
SETT="$BASE/settings.py"
if [ ! -f "$SETT" ]; then
cat > "$SETT" <<'PY'
from pydantic import BaseModel
import os

class Settings(BaseModel):
    API_PREFIX: str = "/api/seedtest"
    JWKS_URL: str = os.getenv("JWKS_URL", "https://auth.dreamseedai.com/.well-known/jwks.json")
    JWT_ISS: str = os.getenv("JWT_ISS", "https://auth.dreamseedai.com/")
    JWT_AUD: str = os.getenv("JWT_AUD", "seedtest-api")
    LOCAL_DEV: bool = os.getenv("LOCAL_DEV", "false").lower() == "true"

settings = Settings()
PY
fi

# security/jwt.py
SEC="$BASE/security/jwt.py"
if [ ! -f "$SEC" ]; then
cat > "$SEC" <<'PY'
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
import httpx, time
from typing import Dict
from settings import settings

_jwks = {"exp": 0, "keys": []}
bearer = HTTPBearer(auto_error=False)

async def get_jwks():
    now = int(time.time())
    if now < _jwks["exp"]:
        return _jwks["keys"]
    async with httpx.AsyncClient(timeout=3) as client:
        r = await client.get(settings.JWKS_URL)
    r.raise_for_status()
    data = r.json()
    _jwks["keys"] = data["keys"]
    _jwks["exp"] = now + 3600
    return _jwks["keys"]

async def decode_token(token: str) -> Dict:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for key in await get_jwks():
        if key["kid"] == kid:
            return jwt.decode(
                token,
                key,
                audience=settings.JWT_AUD,
                issuer=settings.JWT_ISS,
                algorithms=["RS256"],
                options={"verify_at_hash": False},
            )
    raise HTTPException(status_code=401, detail="Invalid token (kid)")

def require_scopes(*required):
    async def checker(creds: HTTPAuthorizationCredentials = Security(bearer)):
        if settings.LOCAL_DEV and not creds:
            return {"sub":"dev-user","org_id":1,"scope":"exam:read exam:write","roles":["student"]}
        if not creds:
            raise HTTPException(401, "Missing Authorization")
        payload = await decode_token(creds.credentials)
        token_scopes = set((payload.get("scope") or "").split())
        if not set(required).issubset(token_scopes):
            raise HTTPException(403, "insufficient_scope")
        return payload
    return checker

def same_org_guard(payload: Dict, org_id: int):
    if payload.get("roles") and "admin" in payload["roles"]:
        return
    if int(payload.get("org_id", -1)) != int(org_id):
        raise HTTPException(403, "forbidden_org")
PY
fi

# schemas/exams.py
SCH="$BASE/schemas/exams.py"
if [ ! -f "$SCH" ]; then
cat > "$SCH" <<'PY'
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict

class CreateExamRequest(BaseModel):
    exam_id: str
    mode: Optional[str] = None

class CreateExamResponse(BaseModel):
    exam_session_id: str
    start_time: str
    exam_id: str

class QuestionOut(BaseModel):
    id: str
    text: str
    type: Literal['mcq','text','multi']
    options: Optional[List[str]] = None
    timer_sec: Optional[int] = None

class NextQuestionResponse(BaseModel):
    done: bool
    next_difficulty: Optional[int] = None
    question: Optional[QuestionOut] = None
    result: Optional[Dict] = None
    finished: Optional[bool] = None

class AnswerSubmission(BaseModel):
    question_id: str
    answer: Optional[str] = None
    elapsed_time: Optional[float] = Field(default=None, description="seconds")

class NextStepRequest(BaseModel):
    session_id: str
    last_question_id: Optional[Dict] = None
    last_answer: Optional[Dict] = None
    difficulty: Optional[int] = None
PY
fi

# services/adaptive_engine.py
SVC="$BASE/services/adaptive_engine.py"
if [ ! -f "$SVC" ]; then
cat > "$SVC" <<'PY'
import time
from typing import Dict, Optional

_sessions: Dict[str, Dict] = {}

def start_session(exam_id:str, user_id:str, org_id:int) -> Dict:
    session_id = f"sess_{int(time.time()*1000)}"
    _sessions[session_id] = {
        "exam_id": exam_id, "user_id":user_id, "org_id": org_id,
        "index": 0, "theta": 0.0, "done": False
    }
    return {"exam_session_id": session_id, "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "exam_id": exam_id}

def select_next(session_id:str) -> Optional[Dict]:
    s = _sessions.get(session_id)
    if not s:
        return None
    if s["index"] >= 10:
        s["done"] = True
        return None
    qid = f"q{s['index']+1}"
    q = {
        "id": qid,
        "text": f"{s['index']+1} + {s['index']+2} = ?",
        "type": "mcq",
        "options": ["1","2","3","4"]
    }
    return q

def submit_answer(session_id:str, question_id:str, answer:str, elapsed:float=None) -> Dict:
    s = _sessions.get(session_id)
    if not s:
        return {"error":"not_found"}
    correct = (answer == "3")
    s["theta"] += 0.1 if correct else -0.1
    s["index"] += 1
    if s["index"] >= 10:
        s["done"] = True
        return {"finished": True, "result": {"score": max(0, int((s['theta']+1)*50)), "correct": s["index"], "incorrect": 10-s["index"]}}
    return {"correct": correct, "updated_theta": s["theta"]}
PY
fi

# routers/exams.py
RT="$BASE/routers/exams.py"
if [ ! -f "$RT" ]; then
cat > "$RT" <<'PY'
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from schemas.exams import *
from security.jwt import require_scopes
from services.adaptive_engine import start_session, select_next, submit_answer

router = APIRouter(prefix="/api/seedtest", tags=["exams"])

@router.post("/exams", response_model=CreateExamResponse, summary="Create exam session")
async def create_exam(body: CreateExamRequest, payload=Depends(require_scopes("exam:write"))):
    org_id = int(payload.get("org_id", -1))
    if org_id < 0:
        raise HTTPException(403, "missing_org")
    return start_session(body.exam_id, payload["sub"], org_id)

@router.get("/exams/{session_id}/next", response_model=NextQuestionResponse, summary="Get next question")
async def next_question(session_id: str, payload=Depends(require_scopes("exam:read"))):
    q = select_next(session_id)
    if q is None:
        return {"done": True, "next_difficulty": None}
    return {"done": False, "next_difficulty": 3, "question": q}

@router.post("/exams/{session_id}/response", response_model=NextQuestionResponse, summary="Submit answer and get next")
async def submit(session_id: str, body: AnswerSubmission, payload=Depends(require_scopes("exam:write")),
                 idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    res = submit_answer(session_id, body.question_id, body.answer or "", body.elapsed_time)
    if "error" in res:
        raise HTTPException(404, "session_not_found")
    if res.get("finished"):
        return {"done": True, "result": res["result"], "next_difficulty": 3}
    q = select_next(session_id)
    return {"done": False, "next_difficulty": 4, "question": q, **res}

@router.get("/exams/{session_id}/result", summary="Get exam result")
async def result(session_id:str, payload=Depends(require_scopes("exam:read"))):
    return {
      "exam_session_id": session_id,
      "user_id": payload["sub"],
      "score": 128,
      "ability_estimate": 0.55,
      "standard_error": 0.32,
      "percentile": 85,
      "topic_breakdown": [
        {"topic":"대수학", "correct":5, "total":7},
        {"topic":"기하학", "correct":3, "total":5}
      ],
      "recommendations": [
        "확률통계 영역 보완",
        "기하학 풀이 시 그림으로 검증"
      ]
    }

@router.get("/exams", summary="List exam catalog (optional)")
async def list_catalog(payload=Depends(require_scopes("exam:read"))):
    return [{"exam_id":"math_adaptive", "title":"Math Adaptive", "duration":30, "subject":"Math"}]
PY
fi

# middleware/correlation.py
MID="$BASE/middleware/correlation.py"
if [ ! -f "$MID" ]; then
cat > "$MID" <<'PY'
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        cid = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["x-correlation-id"] = cid
        return response
PY
fi

# main.py
MAIN="$BASE/main.py"
if [ ! -f "$MAIN" ]; then
cat > "$MAIN" <<'PY'
from fastapi import FastAPI, Request
from routers.exams import router as exams_router
from middleware.correlation import CorrelationIdMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="SeedTest API",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(CorrelationIdMiddleware)
app.include_router(exams_router)

@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
PY
fi

# 로컬 실행 스크립트
RUN="scripts/run_seedtest_api.sh"
if [ ! -f "$RUN" ]; then
cat > "$RUN" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd apps/seedtest-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export LOCAL_DEV=true
uvicorn main:app --reload --port 8000
SH
chmod +x "$RUN"
fi

echo "✅ Files generated. Creating commit..."

git add "$BASE" scripts/init_seedtest_api_scaffold.sh "$RUN"
git commit -m "feat(api): add FastAPI + OpenAPI scaffold for examinee test interface" || true

# Push branch (create remote if needed)
git push -u origin "$BRANCH_NAME" || true

# PR 생성
if [ -n "$REVIEWERS" ]; then
  gh pr create -B main -t "$PR_TITLE" -b "$PR_BODY" --reviewer "$REVIEWERS"
else
  gh pr create -B main -t "$PR_TITLE" -b "$PR_BODY"
fi

echo "✅ PR created. Run locally: bash scripts/run_seedtest_api.sh"


