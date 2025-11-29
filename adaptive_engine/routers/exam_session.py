from typing import Any, Dict, List, Optional, Set, cast

from fastapi import APIRouter
import time

from adaptive_engine.models.schemas import (
    AnswerRequest,
    AnswerResponse,
    FinishRequest,
    FinishResponse,
    NextRequest,
    NextResponse,
    Question,
    StartRequest,
    StartResponse,
)
from adaptive_engine.services.ability_estimator import (
    estimate_standard_error,
    update_theta,
    estimate_theta,
)
from adaptive_engine.utils.irt_math import fisher_information
from adaptive_engine.services.feedback_generator import generate_feedback, generate_detailed_feedback
from adaptive_engine.services.db_enrichment import enrich_finish_payload
from adaptive_engine.services.item_selector import select_next_question
from adaptive_engine.services.initial_theta import get_initial_theta
from adaptive_engine.services.stop_rules import should_stop
from adaptive_engine.services.session_repo import get_session_repo
from adaptive_engine.models.session import AnsweredItem, SessionState
from adaptive_engine.config import get_selection_policy, get_settings
from adaptive_engine.services.telemetry import log_exposure, log_response, get_overexposed_question_ids


router = APIRouter(prefix="/api/exam", tags=["exam-session"])


@router.post("/start", response_model=StartResponse)
def start_exam(payload: StartRequest) -> StartResponse:
    repo = get_session_repo()
    theta0 = get_initial_theta(payload.user_id, payload.exam_id)
    state = repo.create(user_id=payload.user_id, exam_id=payload.exam_id, time_limit_sec=None)
    state.theta = theta0
    _s = get_settings()
    state.prior_mean = getattr(_s, "estimator_prior_mean", 0.0)
    state.prior_sd = getattr(_s, "estimator_prior_sd", 1.0)
    # timing
    state.started_at = time.time()
    state.last_answer_at = state.started_at
    # initialize histories with initial theta; SE unknown yet
    state.theta_history.append(state.theta)
    repo.save(state)
    return StartResponse(session_id=state.session_id, theta=state.theta, status="started")


@router.get("/state", response_model=dict)
def get_state(session_id: str) -> dict:
    repo = get_session_repo()
    state = repo.get(session_id)
    if not state:
        return {"error": "session not found"}
    # compute elapsed/remaining time
    now_ts = time.time()
    elapsed = None
    if getattr(state, "started_at", None):
        try:
            elapsed = max(0.0, float(now_ts - float(state.started_at or 0)))
        except Exception:
            elapsed = None
    # Remaining time based on settings stop_time_limit_sec
    s = get_settings()
    time_limit = getattr(s, "stop_time_limit_sec", None)
    remaining = None
    if time_limit is not None and elapsed is not None:
        try:
            remaining = max(0.0, float(time_limit) - float(elapsed))
        except Exception:
            remaining = None
    return {
        "session_id": state.session_id,
        "user_id": state.user_id,
        "exam_id": state.exam_id,
        "theta": state.theta,
        "prior": {"mean": state.prior_mean, "sd": state.prior_sd},
        "answered_count": len(state.answered),
        "seen_ids": state.seen_ids,
        "topic_counts": state.topic_counts,
        "theta_history": state.theta_history,
        "se_history": state.se_history,
        "elapsed_time_sec": elapsed,
        "remaining_time_sec": remaining,
    }


@router.post("/next", response_model=NextResponse)
def get_next_question(payload: NextRequest, session_id: str | None = None) -> NextResponse:
    # If session_id provided, prefer session theta and seen_ids/topic_counts
    t = payload.theta
    seen_ids = payload.seen_ids
    topic_counts = None
    state: Optional["SessionState"] = None  # forward ref type comment to avoid import cycle
    if session_id:
        repo = get_session_repo()
        state = repo.get(session_id)
        if state:
            t = state.theta
            seen_ids = state.seen_ids
            topic_counts = state.topic_counts

    policy = get_selection_policy()
    questions = [q.model_dump() for q in payload.available_questions]
    # First-item heuristic: if no seen_ids, prefer difficulty near theta (b closest to t)
    next_q_dict = None
    if not seen_ids:
        candidates = [q for q in questions]
        if candidates:
            next_q_dict = min(candidates, key=lambda q: abs(float(q.get("b", 0.0) or 0.0) - float(t)))
    if next_q_dict is None:
        # Build global exclusion set based on recent exposure, if configured
        exclude_ids = set()
        s = None
        try:
            from adaptive_engine.config import get_settings as _gs
            s = _gs()
        except Exception:
            s = None
        if s and s.exposure_max_per_window and s.exposure_window_hours > 0:
            exclude_ids = get_overexposed_question_ids(s.exposure_max_per_window, s.exposure_window_hours)
        exclude_ids_mixed: Set[str | int] = cast(Set[str | int], exclude_ids)
        next_q_dict = select_next_question(
            t,
            questions,
            seen_ids,
            topic_counts=topic_counts,
            max_per_topic=policy.max_per_topic,
            prefer_balanced=policy.prefer_balanced,
            deterministic=policy.deterministic,
            top_k_random=getattr(policy, "top_k_random", None),
            avoid_topic=(state.last_topic if state else None),
            info_band_fraction=getattr(policy, "info_band_fraction", 0.05),
            exclude_ids=exclude_ids_mixed,
        )
    next_q = Question(**next_q_dict) if next_q_dict else None
    # Log exposure if we have a session context
    if next_q is not None and session_id:
        repo = get_session_repo()
        state = repo.get(session_id)
        if state:
            log_exposure(session_id, state.user_id, state.exam_id, next_q.question_id)
    return NextResponse(question=next_q)


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerRequest, session_id: str | None = None) -> AnswerResponse:
    q = payload.question
    base_theta = payload.theta
    answered_items = list(payload.answered_items)
    state = None
    repo = None
    if session_id:
        repo = get_session_repo()
        state = repo.get(session_id)
        if state:
            base_theta = state.theta
            answered_items = [{"info": it.info} for it in state.answered]

    # Determine estimator method
    s = get_settings()
    method = getattr(s, "estimator_method", "online").lower()
    # Build responses for batch estimators
    responses = []
    if state is not None:
        responses = [
            {"a": it.a, "b": it.b, "c": it.c, "correct": it.is_correct}
            for it in state.answered
        ]
    # include current response in estimation set
    responses = list(responses) + [{"a": float(q.a), "b": float(q.b), "c": float(q.c), "correct": bool(payload.correct)}]

    if method == "online":
        new_theta = update_theta(base_theta, float(q.a), float(q.b), float(q.c), bool(payload.correct))
    elif method in ("mle", "map", "eap"):
        prior_mu = state.prior_mean if state is not None else 0.0
        prior_sd = state.prior_sd if state is not None else 1.0
        new_theta = estimate_theta(
            responses,
            method=method,
            theta0=base_theta,
            prior_mu=prior_mu,
            prior_sigma=prior_sd,
        )
    else:
        new_theta = update_theta(base_theta, float(q.a), float(q.b), float(q.c), bool(payload.correct))
    # Use true Fisher information at the updated theta for the answered item
    info = float(fisher_information(new_theta, float(q.a), float(q.b), float(q.c)))
    answered_items = list(answered_items) + [{"info": info}]
    std_error = estimate_standard_error(new_theta, answered_items)
    # Use settings for stopping thresholds
    _s = get_settings()
    max_items = getattr(_s, "stop_max_items", 20)
    time_limit = getattr(_s, "stop_time_limit_sec", 60)
    se_threshold = getattr(_s, "stop_se_threshold", 0.3)
    # compute elapsed time if session started
    now_ts = time.time()
    elapsed = 0.0
    if state is not None and getattr(state, "started_at", None):
        try:
            elapsed = max(0.0, float(now_ts - float(state.started_at or 0)))
        except Exception:
            elapsed = 0.0
    stop = should_stop(len(answered_items), max_items, elapsed, time_limit, std_error, threshold=se_threshold)

    if state is not None:
        # update session state
        state.theta = new_theta
        state.seen_ids.append(q.question_id)
        topic = q.topic or q.topic_name or "General"
        state.topic_counts[topic] = state.topic_counts.get(topic, 0) + 1
        state.last_topic = topic
        state.answered.append(
            AnsweredItem(
                question_id=q.question_id,
                a=q.a,
                b=q.b,
                c=q.c,
                is_correct=bool(payload.correct),
                info=info,
            )
        )
        # record histories
        state.theta_history.append(new_theta)
        state.se_history.append(std_error)
        state.last_answer_at = now_ts
        if repo is not None:
            repo.save(state)
        # log response (session_id is not None here due to earlier guard)
        if session_id is not None:
            log_response(session_id, state.user_id, state.exam_id, q.question_id, bool(payload.correct), ability_after=new_theta)

    return AnswerResponse(theta_after=new_theta, std_error=std_error, stop=stop)


def _persist_exam_completion(session_id: str, user_id: int, exam_id: int, theta: float | None, se: float | None, scaled_score: float | None) -> None:
    s = get_settings()
    if not s.database_url:
        return
    try:
        import psycopg2  # type: ignore
    except Exception:
        return
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO exam_sessions (session_id, exam_id, user_id, end_time, ability_estimate, standard_error, final_score, completed)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, TRUE)
                ON CONFLICT (session_id)
                DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    ability_estimate = EXCLUDED.ability_estimate,
                    standard_error = EXCLUDED.standard_error,
                    final_score = EXCLUDED.final_score,
                    completed = TRUE
                """,
                (
                    session_id,
                    int(exam_id),
                    int(user_id),
                    (float(theta) if theta is not None else None),
                    (float(se) if se is not None else None),
                    (float(scaled_score) if scaled_score is not None else None),
                ),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception:
        return


@router.post("/finish", response_model=FinishResponse)
def finish_exam(payload: FinishRequest, session_id: str | None = None) -> FinishResponse:
    # Convert questions into an id->question dict for feedback utility
    qmap: Dict[Any, Dict[str, Any]] = {}
    if isinstance(payload.questions, list):
        qmap = {q.question_id: q.model_dump() for q in payload.questions}
    else:
        for k, v in payload.questions.items():
            if isinstance(v, Question):
                qmap[k] = v.model_dump()
            elif isinstance(v, dict):
                qmap[k] = v
            else:
                # Best-effort coercion
                try:
                    qmap[k] = Question.model_validate(v).model_dump()  # type: ignore[arg-type]
                except Exception:
                    qmap[k] = {"question_id": k}
    feedback = generate_feedback(payload.responses, qmap)
    # Optionally compute final metrics using session state
    theta_final: float | None = None
    se_final: float | None = None
    scaled: float | None = None
    if session_id:
        repo = get_session_repo()
        st = repo.get(session_id)
        if st:
            theta_final = float(st.theta)
            # prefer recorded SE history
            if st.se_history:
                se_final = float(st.se_history[-1])
            else:
                # fallback: sum info of answered
                infos = [float(it.info) for it in st.answered if getattr(it, "info", 0) > 0]
                if infos:
                    import math as _m
                    se_final = float((_m.sqrt(1.0 / sum(infos))))
            s = get_settings()
            scaled = float(getattr(s, "scale_mean_ref", 100.0)) + float(getattr(s, "scale_sd_ref", 15.0)) * float(theta_final)
            # Best-effort persistence to DB
            try:
                _persist_exam_completion(session_id, st.user_id, st.exam_id, theta_final, se_final, scaled)
            except Exception:
                pass
    # 95% CI if possible
    ci = None
    if theta_final is not None and se_final is not None:
        z = 1.96
        ci = {"level": 0.95, "lower": float(theta_final - z * se_final), "upper": float(theta_final + z * se_final)}
    # Build detailed sections (items review, topic breakdown, recommendations) and percentile
    detailed = generate_detailed_feedback(payload.responses, qmap, theta=theta_final, se=se_final, scaled_score=scaled)
    # Enrich with DB-backed solution_html and topic averages when configured
    enriched = enrich_finish_payload({
        "items_review": detailed.get("items_review"),
        "topic_breakdown": detailed.get("topic_breakdown"),
    })
    percentile = detailed.get("summary", {}).get("percentile")
    return FinishResponse(
        feedback=feedback,
        status="completed",
        theta=theta_final,
        se=se_final,
        scaled_score=scaled,
        ci=ci,
        percentile=percentile if isinstance(percentile, (int, float)) else None,
        items_review=enriched.get("items_review"),
        topic_breakdown=enriched.get("topic_breakdown"),
        recommendations=detailed.get("recommendations"),
    )
