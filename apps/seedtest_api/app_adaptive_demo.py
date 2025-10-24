# flake8: noqa
from __future__ import annotations

import math
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.irt import (
    irf_3pl,
    mle_update_one_step,
    update_test_info_and_se,
)
from apps.seedtest_api.services.adaptive import choose_next_question, _make_prefilter
from apps.seedtest_api.services.acceptance_loader import load_acceptance_probs
from shared.adaptive import select_next_with_constraints, KeyMap

# Note: settings are fetched within handlers to respect test-time monkeypatch+reload


app = FastAPI(title="SeedTest Adaptive Demo")


class StartRequest(BaseModel):
    theta0: float = 0.0
    topic_ids: Optional[List[int]] = None
    tags_any: Optional[List[str]] = None


class StartResponse(BaseModel):
    session_id: str
    theta: float
    next_item_id: Optional[int]
    next_item_info: Optional[float]
    policy: Optional[dict] = None
    started_at: Optional[float] = None


class AnswerRequest(BaseModel):
    item_id: int
    correct: bool
    # Optional manual termination request (e.g., from a "Finish Now" UI)
    finish_now: Optional[bool] = False
    # Optionally provide client-side time remaining or elapsed; server uses server-side start time when available
    client_elapsed_seconds: Optional[float] = None


class AnswerResponse(BaseModel):
    theta: float
    se: float
    next_item_id: Optional[int]
    reason: Optional[str] = None
    terminated: bool = False
    items_answered: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    cooldown_remaining: Optional[float] = None


# In-memory short-lived store for demo purposes only
SESSIONS: Dict[str, Dict] = {}


# Minimal demo item pool (replace with DB-backed source)
DEMO_POOL: List[Dict] = [
    {
        "question_id": 1,
        "discrimination": 1.2,
        "difficulty": -0.5,
        "guessing": 0.2,
        "topic_id": 10,
        "tags": ["algebra"],
    },
    {
        "question_id": 2,
        "discrimination": 1.0,
        "difficulty": 0.0,
        "guessing": 0.2,
        "topic_id": 10,
        "tags": ["algebra", "functions"],
    },
    {
        "question_id": 3,
        "discrimination": 1.4,
        "difficulty": 0.5,
        "guessing": 0.2,
        "topic_id": 20,
        "tags": ["geometry"],
    },
    {
        "question_id": 4,
        "discrimination": 0.9,
        "difficulty": 1.0,
        "guessing": 0.2,
        "topic_id": 20,
        "tags": ["geometry"],
    },
]


def _gen_session_id() -> str:
    import time, random

    return f"sess_{int(time.time()*1000)}_{random.randint(1000,9999)}"


@app.post("/demo/start", response_model=StartResponse)
def start_session(req: StartRequest) -> StartResponse:
    # Fetch latest settings to honor test-time env changes
    from apps.seedtest_api.settings import Settings

    settings = Settings()
    sid = _gen_session_id()
    theta = float(req.theta0)
    test_info = 0.0
    used_ids: List[int] = []
    import time

    started_at = time.time()

    # Pick the first item
    try:
        # Use constrained selector with settings-driven knobs
        km = KeyMap(id="question_id", a="discrimination", b="difficulty", c="guessing")
        pre = _make_prefilter(topic_ids=req.topic_ids, tags_any=req.tags_any)
        # Optional blueprint parsing
        bp = None
        if settings.CAT_BLUEPRINT:
            import json

            try:
                raw = json.loads(settings.CAT_BLUEPRINT)
                # Coerce keys to int when possible
                bp = {}
                for k, v in (raw or {}).items():
                    try:
                        kk = int(k)
                    except Exception:
                        kk = k
                    bp[kk] = float(v)
            except Exception:
                bp = None
        # Optional start randomization: filter by difficulty band and randomize among top-N at theta0
        import random

        start_items = DEMO_POOL
        if settings.CAT_START_RANDOMIZED:
            band = float(settings.CAT_START_BAND_WIDTH)
            lo, hi = float(req.theta0) - band, float(req.theta0) + band
            start_items = [
                it for it in DEMO_POOL if lo <= float(it.get("difficulty", 0.0)) <= hi
            ] or DEMO_POOL
        item, info, _ = select_next_with_constraints(
            theta,
            start_items,
            used_ids=used_ids,
            keymap=km,
            prefilter=pre,
            top_n=max(
                int(
                    settings.CAT_START_TOP_N
                    if settings.CAT_START_RANDOMIZED
                    else settings.CAT_TOP_N
                ),
                1,
            ),
            exposure_counts=None,
            max_exposure=settings.CAT_MAX_EXPOSURE,
            acceptance_probs=load_acceptance_probs(settings.CAT_ACCEPTANCE_SOURCE),
            last_topics=[],
            topic_key="topic_id",
            avoid_repeat_k=max(int(settings.CAT_AVOID_REPEAT_K), 0),
            repeat_penalty=float(settings.CAT_REPEAT_PENALTY),
            content_blueprint=bp,
            content_counts=None,
            avoid_same_topic_hard=bool(settings.CAT_AVOID_SAME_TOPIC_HARD),
            same_topic_tolerance=float(settings.CAT_SAME_TOPIC_TOLERANCE),
            default_acceptance_p=settings.CAT_ACCEPTANCE_P_DEFAULT,
        )
        next_id = item["question_id"]
    except Exception:
        item, info, next_id = None, None, None

    SESSIONS[sid] = {
        "theta": theta,
        "test_info": test_info,
        "used_ids": used_ids,
        "topic_ids": req.topic_ids or [],
        "tags_any": req.tags_any or [],
        # Track simple exposure and content counts for demo
        "exposure_counts": {},
        "content_counts": {},
        "last_topics": [],
        "started_at": started_at,
    }

    pol = {
        "top_n": settings.CAT_TOP_N,
        "avoid_repeat_k": settings.CAT_AVOID_REPEAT_K,
        "repeat_penalty": settings.CAT_REPEAT_PENALTY,
        "max_exposure": settings.CAT_MAX_EXPOSURE,
        # Stop-rule policy
        "mode": settings.CAT_MODE,
        "sem_threshold": settings.CAT_SEM_THRESHOLD,
        "min_items": settings.CAT_MIN_ITEMS,
        "max_items": settings.CAT_MAX_ITEMS,
        "max_time_seconds": settings.CAT_MAX_TIME_SECONDS,
        "min_test_time_seconds": settings.CAT_MIN_TEST_TIME_SECONDS,
        "item_cooldown_seconds": settings.CAT_ITEM_COOLDOWN_SECONDS,
    }
    return StartResponse(
        session_id=sid,
        theta=theta,
        next_item_id=next_id,
        next_item_info=info,
        policy=pol,
        started_at=started_at,
    )


@app.post("/demo/answer/{session_id}", response_model=AnswerResponse)
def answer(session_id: str, req: AnswerRequest) -> AnswerResponse:
    # Fetch latest settings to honor test-time env changes
    from apps.seedtest_api.settings import Settings

    settings = Settings()
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")

    theta = float(s["theta"])
    test_info = float(s["test_info"])
    used_ids: List[int] = list(s["used_ids"])  # copy

    # Look up item params from pool (demo lookup; replace with DB)
    item = next((it for it in DEMO_POOL if it["question_id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=400, detail="unknown item id")

    a = float(item["discrimination"])
    b = float(item["difficulty"])
    c = float(item.get("guessing", 0.0))
    y = 1 if req.correct else 0

    # One-step MLE update for speed
    theta_new, _, _, _ = mle_update_one_step(theta, a, b, c, y)
    # Accumulate info and compute SE at updated theta
    test_info_new, se = update_test_info_and_se(theta_new, a, b, c, test_info)

    used_ids.append(req.item_id)

    # Update demo exposure/content tracking
    exp = s.get("exposure_counts", {})
    exp[req.item_id] = exp.get(req.item_id, 0) + 1
    s["exposure_counts"] = exp
    cnt = s.get("content_counts", {})
    tkey = item.get("topic_id")
    if tkey is not None:
        cnt[tkey] = cnt.get(tkey, 0) + 1
        s.setdefault("last_topics", [])
        s["last_topics"].append(tkey)
        # keep last K
        k = max(int(settings.CAT_AVOID_REPEAT_K), 0)
        if k > 0:
            s["last_topics"] = s["last_topics"][-k:]
    s["content_counts"] = cnt

    # Stopping criteria evaluation
    import time

    started_at = s.get("started_at")
    elapsed = float(time.time() - started_at) if started_at else None
    items_answered = len(used_ids)

    # Determine configured thresholds/modes
    sem_threshold = (
        float(settings.CAT_SEM_THRESHOLD)
        if settings.CAT_SEM_THRESHOLD is not None
        else None
    )
    max_items = (
        int(settings.CAT_MAX_ITEMS) if settings.CAT_MAX_ITEMS is not None else None
    )
    min_items = int(settings.CAT_MIN_ITEMS) if settings.CAT_MIN_ITEMS is not None else 1
    max_time = (
        int(settings.CAT_MAX_TIME_SECONDS)
        if settings.CAT_MAX_TIME_SECONDS is not None
        else None
    )

    # Item cooldown: defer next selection until cooldown elapses
    last_answer_at = s.get("last_answer_at")
    cooldown = settings.CAT_ITEM_COOLDOWN_SECONDS
    if cooldown is not None:
        now_ts = time.time()
        if last_answer_at is None:
            # First answer: start cooldown immediately and withhold next item
            s.update(
                {
                    "theta": theta_new,
                    "test_info": test_info_new,
                    "used_ids": used_ids,
                    "last_answer_at": now_ts,
                }
            )
            return AnswerResponse(
                theta=theta_new,
                se=se,
                next_item_id=None,
                reason="cooldown",
                terminated=False,
                items_answered=items_answered,
                elapsed_seconds=elapsed,
                cooldown_remaining=float(cooldown),
            )
        else:
            since = now_ts - float(last_answer_at)
            if since < float(cooldown):
                s.update(
                    {
                        "theta": theta_new,
                        "test_info": test_info_new,
                        "used_ids": used_ids,
                    }
                )
                return AnswerResponse(
                    theta=theta_new,
                    se=se,
                    next_item_id=None,
                    reason="cooldown",
                    terminated=False,
                    items_answered=items_answered,
                    elapsed_seconds=elapsed,
                    cooldown_remaining=float(cooldown - since),
                )

    # Manual termination takes precedence if allowed
    if req.finish_now:
        s.update({"theta": theta_new, "test_info": test_info_new, "used_ids": used_ids})
        return AnswerResponse(
            theta=theta_new,
            se=se,
            next_item_id=None,
            reason="manual_finish",
            terminated=True,
            items_answered=items_answered,
            elapsed_seconds=elapsed,
        )

    # Fixed-length mode: stop when items reach max (if set)
    if (
        settings.CAT_MODE == "FIXED"
        and max_items is not None
        and items_answered >= max_items
    ):
        s.update({"theta": theta_new, "test_info": test_info_new, "used_ids": used_ids})
        return AnswerResponse(
            theta=theta_new,
            se=se,
            next_item_id=None,
            reason="max_items",
            terminated=True,
            items_answered=items_answered,
            elapsed_seconds=elapsed,
        )

    # Time limit
    if max_time is not None and elapsed is not None and elapsed >= max_time:
        s.update({"theta": theta_new, "test_info": test_info_new, "used_ids": used_ids})
        return AnswerResponse(
            theta=theta_new,
            se=se,
            next_item_id=None,
            reason="time_limit",
            terminated=True,
            items_answered=items_answered,
            elapsed_seconds=elapsed,
        )

    # Variable-length precision stop (after at least min_items); gate by minimum test time if provided
    if (
        settings.CAT_MODE == "VARIABLE"
        and sem_threshold is not None
        and items_answered >= max(min_items, 1)
        and se <= sem_threshold
    ):
        min_time = settings.CAT_MIN_TEST_TIME_SECONDS
        if min_time is not None and elapsed is not None and elapsed < float(min_time):
            # Not enough elapsed time yet; continue
            pass
        else:
            s.update(
                {"theta": theta_new, "test_info": test_info_new, "used_ids": used_ids}
            )
            return AnswerResponse(
                theta=theta_new,
                se=se,
                next_item_id=None,
                reason="sem_threshold",
                terminated=True,
                items_answered=items_answered,
                elapsed_seconds=elapsed,
            )

    # Choose next using constrained selector
    try:
        km = KeyMap(id="question_id", a="discrimination", b="difficulty", c="guessing")
        pre = (
            _make_prefilter(topic_ids=s["topic_ids"], tags_any=s["tags_any"])
            if (s.get("topic_ids") or s.get("tags_any"))
            else None
        )
        bp = None
        if settings.CAT_BLUEPRINT:
            import json

            try:
                raw = json.loads(settings.CAT_BLUEPRINT)
                bp = {}
                for k, v in (raw or {}).items():
                    try:
                        kk = int(k)
                    except Exception:
                        kk = k
                    bp[kk] = float(v)
            except Exception:
                bp = None
        item_next, info_next, _ = select_next_with_constraints(
            theta_new,
            DEMO_POOL,
            used_ids=used_ids,
            keymap=km,
            prefilter=pre,
            top_n=max(int(settings.CAT_TOP_N), 1),
            exposure_counts=s.get("exposure_counts"),
            max_exposure=settings.CAT_MAX_EXPOSURE,
            acceptance_probs=load_acceptance_probs(settings.CAT_ACCEPTANCE_SOURCE),
            last_topics=s.get("last_topics"),
            topic_key="topic_id",
            avoid_repeat_k=max(int(settings.CAT_AVOID_REPEAT_K), 0),
            repeat_penalty=float(settings.CAT_REPEAT_PENALTY),
            content_blueprint=bp,  # parsed from settings.CAT_BLUEPRINT when provided
            content_counts=s.get("content_counts"),
            avoid_same_topic_hard=bool(settings.CAT_AVOID_SAME_TOPIC_HARD),
            same_topic_tolerance=float(settings.CAT_SAME_TOPIC_TOLERANCE),
            default_acceptance_p=settings.CAT_ACCEPTANCE_P_DEFAULT,
        )
        next_id = item_next["question_id"]
        reason = None
    except Exception:
        # No more items available
        next_id, info_next, reason = None, None, "pool_exhausted"

    # Exposure logging (demo: append to file if configured)
    try:
        if settings.CAT_EXPOSURE_LOG_PATH:
            with open(settings.CAT_EXPOSURE_LOG_PATH, "a") as f:
                import time as _t

                f.write(f"{session_id}\t{req.item_id}\t{_t.time()}\n")
    except Exception:
        pass

    # Persist back
    s.update(
        {
            "theta": theta_new,
            "test_info": test_info_new,
            "used_ids": used_ids,
            "last_answer_at": time.time(),
        }
    )

    return AnswerResponse(theta=theta_new, se=se, next_item_id=next_id, reason=reason)


# To run locally (optional):
# uvicorn apps.seedtest_api.app_adaptive_demo:app --reload --port 8009
