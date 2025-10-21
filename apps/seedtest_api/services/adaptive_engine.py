from typing import Optional, List, Tuple, Dict
from ..schemas.exams import QuestionOut
import time
import math


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
        return QuestionOut(id="q_easy", text="2 + 2 = ?", type="mcq", options=["2","3","4","5"], timer_sec=60)
    return QuestionOut(id="q_hard", text="12 + 13 = ?", type="mcq", options=["22","24","25","26"], timer_sec=60)

# ------------------- In-memory adaptive session stub -------------------

_sessions: Dict[str, Dict] = {}


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
        # simple in-memory item bank (id, a, b, c)
        "bank": [
            {"id": "q1",  "a": 1.00, "b": -1.5, "c": 0.20},
            {"id": "q2",  "a": 0.80, "b": -0.5, "c": 0.20},
            {"id": "q3",  "a": 1.20, "b": 0.0,  "c": 0.20},
            {"id": "q4",  "a": 1.00, "b": 0.5,  "c": 0.20},
            {"id": "q5",  "a": 1.20, "b": 1.0,  "c": 0.20},
            {"id": "q6",  "a": 0.70, "b": 1.5,  "c": 0.20},
            {"id": "q7",  "a": 1.50, "b": -1.0, "c": 0.20},
            {"id": "q8",  "a": 0.90, "b": 2.0,  "c": 0.20},
            {"id": "q9",  "a": 1.30, "b": -2.0, "c": 0.20},
            {"id": "q10", "a": 1.10, "b": 0.8,  "c": 0.20},
        ]
    }
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
    best = max(candidates, key=lambda it: fisher_information_3pl(it["a"], it["b"], it["c"], theta))
    q = {
        "id": best["id"],
        "text": f"Solve item {best['id']}",
        "type": "mcq",
        "options": ["1","2","3","4"]
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
    # 임시 정답 규칙(데모): '3'이면 정답 처리
    correct = (answer == "3")
    # MAP(라플라스 근사) 기반 3PL 베이즈 업데이트
    s["theta"] = bayes_update_theta_3pl(
        theta=s["theta"], a=item["a"], b=item["b"], c=item["c"], u=1 if correct else 0
    )
    s["index"] += 1
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
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    max_iter: int = 5,
    step_cap: float = 1.0,
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
        I = (dP * dP) / max(P * Q, 1e-8)
        H = -(I + 1.0 / (prior_sd * prior_sd))
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


