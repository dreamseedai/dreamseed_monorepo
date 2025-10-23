import math
import os
import random
import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text

from ..schemas.exams import QuestionOut
from ..settings import settings, Settings as _Settings


def score_answer(last_answer: dict) -> Tuple[int, bool]:
    # TODO: replace with real scoring
    correct = bool(last_answer and (last_answer.get('choice', 0) == 2))
    return (1 if correct else 0, correct)


def next_difficulty(current: Optional[int], correct: bool) -> int:
    cur = current or 1
    return max(1, cur + (1 if correct else -1))


def next_question_stub(diff: int) -> QuestionOut:
    # TODO: pick from DB/item bank
    if diff <= 2:
        return QuestionOut(id="q_easy", text="2 + 2 = ?", type="mcq", options=["2", "3", "4", "5"], timer_sec=60)
    return QuestionOut(id="q_hard", text="12 + 13 = ?", type="mcq", options=["22", "24", "25", "26"], timer_sec=60)


# ------------------- In-memory adaptive session stub -------------------
#
# Internal structures and best-effort DB-backed helpers for adaptive demo flows.

_sessions: Dict[str, Dict] = {}
_sa_engine = None
_tags_kind: Optional[str] = None  # 'array' | 'jsonb' | None
_tags_kind_checked_at: float | None = None


def _get_engine():
    global _sa_engine
    if _sa_engine is None and settings.DATABASE_URL:
        _sa_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _sa_engine


def _load_item_bank_from_db(limit: int | None = None) -> List[Dict]:
    eng = _get_engine()
    if not eng:
        return []
    conditions = []
    params: Dict[str, object] = {}
    if settings.BANK_SUBJECT:
        conditions.append("e.subject = :subject")
        params["subject"] = settings.BANK_SUBJECT
    if settings.BANK_ORG_ID is not None:
        conditions.append("(q.org_id = :org OR q.org_id IS NULL)")
        params["org"] = settings.BANK_ORG_ID
    if settings.BANK_DIFF_MIN is not None:
        conditions.append("q.difficulty >= :dmin")
        params["dmin"] = settings.BANK_DIFF_MIN
    if settings.BANK_DIFF_MAX is not None:
        conditions.append("q.difficulty <= :dmax")
        params["dmax"] = settings.BANK_DIFF_MAX
    # topic filter (expects questions.topic_id to exist)
    topic_ids: List[int] = []
    if settings.BANK_TOPIC_IDS:
        for tok in settings.BANK_TOPIC_IDS.replace(",", " ").split():
            try:
                topic_ids.append(int(tok))
            except ValueError:
                continue
        if topic_ids:
            conditions.append("q.topic_id = ANY(:topic_ids)")
            params["topic_ids"] = topic_ids
    # tags filter (assumes questions.tags as text[] or JSONB string array)
    tag_list: List[str] = []
    if settings.BANK_TAGS:
        tag_list = [t for t in settings.BANK_TAGS.replace(",", " ").split() if t]
        if tag_list:
            # detect tags column kind once
            kind = _detect_tags_kind()
            tag_csv = ",".join(tag_list)
            if kind == 'jsonb':
                # jsonb: '?|' operator with text[]; use string_to_array to avoid driver array binding
                conditions.append("(q.tags ?| string_to_array(:tag_csv, ','))")
                params["tag_csv"] = tag_csv
            elif kind == 'array':
                # text[]: '&&' overlaps operator with text[]; use string_to_array
                conditions.append("(q.tags && string_to_array(:tag_csv, ','))")
                params["tag_csv"] = tag_csv
            else:
                # unknown type: skip tag filter defensively
                pass
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT q.question_id AS id,
               COALESCE(q.discrimination, 1.0) AS a,
               COALESCE(q.difficulty, 0.0)    AS b,
               COALESCE(q.guessing, 0.2)      AS c
        FROM questions q
        LEFT JOIN exams e ON 1=1  -- optional subject filter
        {where}
        ORDER BY q.question_id
    """
    if limit:
        sql += " LIMIT :lim"
        params["lim"] = limit
    with eng.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        bank = [dict(r) for r in rows]
    # Random subsampling (K or Bernoulli-p)
    if settings.BANK_SAMPLE_K and settings.BANK_SAMPLE_K > 0:
        bank = random.sample(bank, k=min(settings.BANK_SAMPLE_K, len(bank)))
    elif settings.BANK_SAMPLE_P and 0 < settings.BANK_SAMPLE_P < 1:
        bank = [it for it in bank if random.random() < settings.BANK_SAMPLE_P]
    return bank


def _detect_tags_kind() -> Optional[str]:
    global _tags_kind
    global _tags_kind_checked_at
    now = time.time()
    ttl_val = settings.TAGS_KIND_TTL_SEC
    ttl = 300 if ttl_val is None else ttl_val
    if ttl != 0 and _tags_kind is not None and _tags_kind_checked_at and (now - _tags_kind_checked_at) < ttl:
        return _tags_kind
    eng = _get_engine()
    if not eng:
        return None
    sql = """
        SELECT data_type, udt_name
        FROM information_schema.columns
        WHERE column_name = 'tags' AND table_name = 'questions'
        ORDER BY CASE table_schema WHEN 'public' THEN 0 ELSE 1 END
        LIMIT 1
    """
    try:
        with eng.connect() as conn:
            row = conn.execute(text(sql)).first()
            if not row:
                _tags_kind = None
            else:
                data_type = (row[0] or '').lower()
                udt_name = (row[1] or '').lower()
                if 'jsonb' in (data_type, udt_name):
                    _tags_kind = 'jsonb'
                elif data_type == 'array' or udt_name.startswith('_'):
                    _tags_kind = 'array'
                else:
                    _tags_kind = None
    except Exception:
        _tags_kind = None
    _tags_kind_checked_at = now
    return _tags_kind


def _is_correct_from_db(question_id: str | int, answer_text: str | None) -> Optional[bool]:
    # In LOCAL_DEV mode, avoid hitting DB for correctness; fall back to simple rule
    if _Settings().LOCAL_DEV or (os.getenv("LOCAL_DEV", "false").lower() == "true"):
        return None
    eng = _get_engine()
    if not eng or answer_text is None:
        return None
    # 우선 content 매칭으로 정답 판정
    sql = """
        SELECT is_correct
        FROM choices
        WHERE question_id = :qid AND content = :ans
        LIMIT 1
    """
    with eng.connect() as conn:
        row = conn.execute(text(sql), {"qid": int(question_id), "ans": str(answer_text)}).first()
        if row is not None:
            return bool(row[0])
    return None


def start_session(exam_id: str, user_id: str, org_id: int) -> Dict:
    session_id = f"sess_{int(time.time()*1000)}"
    _sessions[session_id] = {
        "exam_id": exam_id,
        "user_id": user_id,
        "org_id": org_id,
        "index": 0,
        "theta": 0.0,
        "done": False,
        "administered": [],  # list of question ids
        "responses": [],     # list of {question_id, correct, answer, a,b,c, elapsed?}
    }
    # Item bank을 DB에서 로딩(가능 시), 실패/미설정이면 스텁 유지
    try:
        bank = _load_item_bank_from_db()
        if bank:
            _sessions[session_id]["bank"] = bank
        else:
            _sessions[session_id]["bank"] = [
                {"id": "1",  "a": 1.00, "b": -1.5, "c": 0.20},
                {"id": "2",  "a": 0.80, "b": -0.5, "c": 0.20},
                {"id": "3",  "a": 1.20, "b": 0.0,  "c": 0.20},
                {"id": "4",  "a": 1.00, "b": 0.5,  "c": 0.20},
                {"id": "5",  "a": 1.20, "b": 1.0,  "c": 0.20},
            ]
    except Exception:
        _sessions[session_id]["bank"] = [
            {"id": "1",  "a": 1.00, "b": -1.5, "c": 0.20},
            {"id": "2",  "a": 0.80, "b": -0.5, "c": 0.20},
            {"id": "3",  "a": 1.20, "b": 0.0,  "c": 0.20},
            {"id": "4",  "a": 1.00, "b": 0.5,  "c": 0.20},
            {"id": "5",  "a": 1.20, "b": 1.0,  "c": 0.20},
        ]
    return {
        "exam_session_id": session_id,
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exam_id": exam_id
    }


def select_next(session_id: str) -> Optional[Dict]:
    s = _sessions.get(session_id)
    if not s:
        return None
    if s["index"] >= 10:
        s["done"] = True
        return None
    # 3PL 최대 정보 문항 선택 (미출제 항목 중)
    theta = s["theta"]
    candidates = [it for it in s["bank"] if it["id"] not in s["administered"]]
    if not candidates:
        s["done"] = True
        return None
    if settings.CAT_CRITERION == 'KL':
        best = max(
            candidates,
            key=lambda it: kl_information_3pl(
                it["a"], it["b"], it["c"], theta, settings.CAT_KL_DELTA
            ),
        )
    else:
        best = max(candidates, key=lambda it: fisher_information_3pl(it["a"], it["b"], it["c"], theta))
    q = {
        "id": best["id"],
        "text": f"Solve item {best['id']}",
        "type": "mcq",
        "options": ["1", "2", "3", "4"]
    }
    # mark administered
    s["administered"].append(best["id"])
    return q


def submit_answer(session_id: str, question_id: str, answer: str, elapsed: float | None = None) -> Dict:
    s = _sessions.get(session_id)
    if not s:
        return {"error": "not_found"}
    # derive a,b,c from bank (fallback to simple mapping)
    bank_map = {it["id"]: it for it in s.get("bank", [])}
    item = bank_map.get(question_id) or {"a": 1.0, "b": 0.0, "c": 0.2}
    # 실제 정답 조회: choices.is_correct (content 매칭)
    correct_db = _is_correct_from_db(question_id, answer)
    if correct_db is None:
        # 임시 규칙 fallback
        correct = (answer == "3")
    else:
        correct = bool(correct_db)
    # MAP(라플라스 근사) 기반 3PL 베이즈 업데이트
    s["theta"] = bayes_update_theta_3pl(
        theta=s["theta"], a=item["a"], b=item["b"], c=item["c"], u=1 if correct else 0
    )
    s["index"] += 1
    # record response history for reporting
    try:
        s.setdefault("responses", []).append({
            "question_id": question_id,
            "answer": answer,
            "correct": bool(correct),
            "a": float(item.get("a", 1.0)),
            "b": float(item.get("b", 0.0)),
            "c": float(item.get("c", 0.2)),
            "elapsed": float(elapsed) if elapsed is not None else None,
        })
    except Exception:
        # best-effort only
        pass

    if s["index"] >= 10:
        s["done"] = True
        return {
            "finished": True,
            "result": {
                "score": max(0, int((s['theta']+1)*50)),
                "correct": s["index"],
                "incorrect": 10 - s["index"]
            }
        }
    return {"correct": correct, "updated_theta": s["theta"]}


def get_session_state(session_id: str) -> Optional[Dict]:
    """Expose internal session state for reporting endpoints."""
    return _sessions.get(session_id)


# ------------------- 3PL + Bayesian update core -------------------

D_CONST = 1.7  # logistic scaling constant used in IRT


def p_3pl(a: float, b: float, c: float, theta: float) -> float:
    z = D_CONST * a * (theta - b)
    L = 1.0 / (1.0 + math.exp(-z))
    return c + (1.0 - c) * L


def dp_dtheta_3pl(a: float, b: float, c: float, theta: float) -> float:
    z = D_CONST * a * (theta - b)
    L = 1.0 / (1.0 + math.exp(-z))
    return (1.0 - c) * D_CONST * a * L * (1.0 - L)


def fisher_information_3pl(a: float, b: float, c: float, theta: float) -> float:
    P = p_3pl(a, b, c, theta)
    Q = 1.0 - P
    dP = dp_dtheta_3pl(a, b, c, theta)
    # I(θ) = (dP/dθ)^2 / (P(1-P))
    denom = max(P * Q, 1e-8)
    return (dP * dP) / denom


def bayes_update_theta_3pl(
    theta: float,
    a: float,
    b: float,
    c: float,
    u: int,
    prior_mean: float = settings.CAT_PRIOR_MEAN,
    prior_sd: float = settings.CAT_PRIOR_SD,
    max_iter: int = 5,
    step_cap: float = settings.CAT_STEP_CAP,
) -> float:
    """Single-item MAP update using one-step Newton iterations with Fisher approximation.
    u: 1(correct) or 0(incorrect)
    """
    t = float(theta)
    for _ in range(max_iter):
        P = p_3pl(a, b, c, t)
        Q = 1.0 - P
        dP = dp_dtheta_3pl(a, b, c, t)
        # gradient of log posterior ≈ (u-P)/(P(1-P)) * dP - (t-μ)/σ^2
        g = (u - P) * dP / max(P * Q, 1e-8) - (t - prior_mean) / (prior_sd * prior_sd)
        # hessian approx = -(Fisher + 1/σ^2)
        info_val = (dP * dP) / max(P * Q, 1e-8)
        H = -(info_val + 1.0 / (prior_sd * prior_sd))
        if H == 0:
            break
        step = -g / H
        # clamp step to avoid divergence
        step = max(-step_cap, min(step_cap, step))
        t_new = t + step
        # convergence check
        if abs(t_new - t) < 1e-3:
            t = t_new
            break
        t = t_new
    # clamp theta to a reasonable range
    return max(-4.0, min(4.0, t))


def bayes_update_batch(
    theta: float,
    items: List[Dict],
    prior_mean: float = settings.CAT_PRIOR_MEAN,
    prior_sd: float = settings.CAT_PRIOR_SD,
    step_cap: float = settings.CAT_STEP_CAP,
) -> float:
    """
    누적 MAP 업데이트: items = [{"a":...,"b":...,"c":...,"u":0|1}, ...]
    순차적으로 bayes_update_theta_3pl을 적용하여 누적 업데이트합니다.
    """
    t = theta
    for it in items:
        t = bayes_update_theta_3pl(
            theta=t,
            a=float(it.get("a", 1.0)),
            b=float(it.get("b", 0.0)),
            c=float(it.get("c", 0.2)),
            u=int(it.get("u", 0)),
            prior_mean=prior_mean,
            prior_sd=prior_sd,
            step_cap=step_cap,
        )
    return t


def kl_information_3pl(a: float, b: float, c: float, theta: float, delta: float) -> float:
    """Symmetric KL between P(θ) and P(θ+δ) as an information-like criterion."""
    t2 = theta + delta
    p1 = p_3pl(a, b, c, theta)
    p2 = p_3pl(a, b, c, t2)
    eps = 1e-8
    p1 = min(max(p1, eps), 1 - eps)
    p2 = min(max(p2, eps), 1 - eps)
    kl12 = p1 * math.log(p1 / p2) + (1 - p1) * math.log((1 - p1) / (1 - p2))
    kl21 = p2 * math.log(p2 / p1) + (1 - p2) * math.log((1 - p2) / (1 - p1))
    return kl12 + kl21
