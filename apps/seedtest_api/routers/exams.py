from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException

from ..schemas.exams import (
    AnswerSubmission,
    CreateExamRequest,
    CreateExamResponse,
    NextQuestionResponse,
    NextStepRequest,
    QuestionOut,
)
from ..security.jwt import require_scopes
from ..services.adaptive_engine import (
    next_difficulty,
    next_question_stub,
    score_answer,
    select_next,
    start_session,
    submit_answer,
)
from ..services.result_service import finish_exam as compute_result
from ..settings import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["exams"])


# Legacy-style next-question (kept for compatibility)
@router.post("/exams/{exam_id}/next-question", response_model=NextQuestionResponse)
async def next_question(
    exam_id: str,
    payload: NextStepRequest,
    user=Depends(require_scopes('exam:write'))
) -> NextQuestionResponse:
    # TODO: auth/session validation
    # Score last
    if payload.last_answer:
        la = payload.last_answer
        try:
            data = la.model_dump()  # type: ignore[attr-defined]
        except Exception:
            data = la if isinstance(la, dict) else {}
        _, correct = score_answer(data)
        ndiff = next_difficulty(payload.difficulty, correct)
    else:
        _, correct = 0, False
        ndiff = payload.difficulty or 1

    # If finished (demo condition)
    if payload.last_question_id == "q_final":
        return NextQuestionResponse(
            done=True,
            next_difficulty=ndiff,
            question=None,
            result={
                "score": 10,
                "correct": 8,
                "incorrect": 2,
                "duration_sec": 500
            }
        )

    # Next question (stub)
    q = next_question_stub(ndiff)
    return NextQuestionResponse(done=False, next_difficulty=ndiff, question=q)


# Session create (legacy-style path)
@router.post("/exams/{exam_id}/sessions", response_model=CreateExamResponse)
async def create_session(
    exam_id: str,
    req: CreateExamRequest,
    user=Depends(require_scopes('exam:write'))
) -> CreateExamResponse:
    user_id = str(user.get('sub', 'unknown'))
    org_id = int(user.get('org_id', 0))
    return start_session(exam_id, user_id, org_id)  # type: ignore[return-value]


@router.post("/exams/{exam_id}/sessions/{session_id}/answer")
async def submit_answer_route(
    exam_id: str,
    session_id: str,
    payload: AnswerSubmission,
    user=Depends(require_scopes('exam:write'))
) -> dict[str, Any]:
    res = submit_answer(session_id, payload.question_id, payload.answer or "", payload.elapsed_time)
    if res.get("finished"):
        # On finish, compute/persist result immediately (best-effort)
        try:
            uid = str(user.get('sub', "")) if isinstance(user, dict) else None
            compute_result(session_id, force=True, user_id=uid)
        except Exception:
            pass
    return res


@router.get("/exams/{exam_id}/sessions/{session_id}/next", response_model=NextQuestionResponse)
async def get_next_question(
    exam_id: str,
    session_id: str,
    user=Depends(require_scopes('exam:write'))
) -> NextQuestionResponse:
    q = select_next(session_id)
    if not q:
        return NextQuestionResponse(done=True, next_difficulty=None, question=None, result=None)
    return NextQuestionResponse(done=False, next_difficulty=None, question=QuestionOut(**q), result=None)


# New endpoints (flat by session_id)

@router.post("/exams", response_model=CreateExamResponse, summary="Create exam session")
async def create_exam(body: CreateExamRequest, payload=Depends(require_scopes("exam:write"))) -> CreateExamResponse:
    org_id = int(payload.get("org_id", -1))
    if org_id < 0:
        raise HTTPException(403, "missing_org")
    return start_session(body.exam_id, payload.get("sub", "unknown"), org_id)  # type: ignore[return-value]


@router.get("/exams/{session_id}/next", response_model=NextQuestionResponse, summary="Get next question")
async def next_question_by_session(session_id: str, payload=Depends(require_scopes("exam:read"))) -> dict[str, Any]:
    q = select_next(session_id)
    if q is None:
        return {"done": True, "next_difficulty": None}
    return {"done": False, "next_difficulty": 3, "question": q}


@router.post("/exams/{session_id}/response", response_model=NextQuestionResponse, summary="Submit answer and get next")
async def submit_by_session(
    session_id: str,
    body: AnswerSubmission,
    payload=Depends(require_scopes("exam:write")),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
) -> dict[str, Any]:
    res = submit_answer(session_id, body.question_id, body.answer or "", body.elapsed_time)
    if "error" in res:
        raise HTTPException(404, "session_not_found")
    if res.get("finished"):
        # 결과를 즉시 계산/저장(멱등). 에러는 응답에는 영향을 주지 않음.
        try:
            uid = str(payload.get("sub", "")) if isinstance(payload, dict) else None
            compute_result(session_id, force=True, user_id=uid)
        except Exception:
            pass
        return {"done": True, "result": res["result"], "next_difficulty": 3}
    q = select_next(session_id)
    return {"done": False, "next_difficulty": 4, "question": q, **res}


# Result endpoints have moved to routers/results.py to centralize persistence and caching.


@router.get("/exams", summary="List exam catalog (optional)")
async def list_catalog(payload=Depends(require_scopes("exam:read"))) -> list[dict[str, Any]]:
    return [{"exam_id": "math_adaptive", "title": "Math Adaptive", "duration": 30, "subject": "Math"}]


# Admin/debug: finalize a session and compute result (idempotent)
@router.post(
    "/exams/{session_id}/finish",
    summary="Admin: finalize session and compute result (idempotent)",
)
async def finish_session_now(
    session_id: str,
    force: bool = True,
    payload=Depends(require_scopes("exam:write")),
) -> dict[str, Any]:
    try:
        uid = str(payload.get("sub", "")) if isinstance(payload, dict) else None
        out = compute_result(session_id, force=force, user_id=uid)
        return {"ok": True, "status": out.get("status", "ready")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"finish_failed: {e}")
