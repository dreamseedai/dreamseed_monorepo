from fastapi.testclient import TestClient

from adaptive_engine.main import app


client = TestClient(app)


def test_start_next_answer_finish_flow():
    # Start
    r = client.post("/api/exam/start", json={"user_id": 1, "exam_id": 101})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "started"
    assert data["theta"] == 0.0

    # Next
    payload_next = {
        "theta": 0.0,
        "available_questions": [
            {"question_id": 1, "a": 1.2, "b": 0.0, "c": 0.2, "topic": "Algebra"},
            {"question_id": 2, "a": 0.9, "b": -0.2, "c": 0.2, "topic": "Geometry"},
        ],
        "seen_ids": [],
    }
    r = client.post("/api/exam/next", json=payload_next)
    assert r.status_code == 200
    next_q = r.json()["question"]
    assert next_q is not None
    assert "question_id" in next_q

    # Answer
    payload_answer = {
        "theta": 0.0,
        "question": next_q,
        "correct": True,
        "answered_items": [],
    }
    r = client.post("/api/exam/answer", json=payload_answer)
    assert r.status_code == 200
    ans = r.json()
    assert "theta_after" in ans and "std_error" in ans and "stop" in ans

    # Finish
    payload_finish = {
        "responses": [{"question_id": next_q["question_id"], "is_correct": True}],
        "questions": payload_next["available_questions"],
    }
    r = client.post("/api/exam/finish", json=payload_finish)
    assert r.status_code == 200
    fin = r.json()
    assert fin["status"] == "completed"
    assert isinstance(fin["feedback"], list)


def test_sessionful_flow_and_balancing():
    # Start and capture session_id
    r = client.post("/api/exam/start", json={"user_id": 2, "exam_id": 202})
    sid = r.json()["session_id"]

    # Provide questions across two topics; ensure balancing doesn't pick same topic over and over
    questions = [
        {"question_id": f"A{i}", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Algebra"}
        for i in range(3)
    ] + [
        {"question_id": f"G{i}", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Geometry"}
        for i in range(3)
    ]

    seen = []
    topics = []
    theta = 0.0
    for _ in range(4):
        r = client.post("/api/exam/next", params={"session_id": sid}, json={
            "theta": theta,
            "available_questions": questions,
            "seen_ids": seen,
        })
        q = r.json()["question"]
        assert q is not None
        seen.append(q["question_id"])
        topics.append(q.get("topic") or q.get("topic_name"))

        # answer correct to move theta a bit
        r = client.post("/api/exam/answer", params={"session_id": sid}, json={
            "theta": theta,
            "question": q,
            "correct": True,
            "answered_items": [],
        })
        theta = r.json()["theta_after"]

    # Expect both topics to appear (balancing)
    assert "Algebra" in topics and "Geometry" in topics


def test_initial_theta_and_first_item_selection(monkeypatch):
    # Force initial theta to 1.0 by monkeypatching the function used by the router
    import adaptive_engine.routers.exam_session as exam_router
    monkeypatch.setattr(exam_router, "get_initial_theta", lambda user_id, exam_id: 1.0)

    # Start session
    r = client.post("/api/exam/start", json={"user_id": 123, "exam_id": 999})
    sid = r.json()["session_id"]
    assert r.json()["theta"] == 1.0

    # Provide questions with differing b values. Expect first pick near b≈1.0
    questions = [
        {"question_id": "L", "a": 1.0, "b": -1.5, "c": 0.2, "topic": "Gen"},
        {"question_id": "M", "a": 1.0, "b": 0.1, "c": 0.2, "topic": "Gen"},
        {"question_id": "H", "a": 1.0, "b": 0.9, "c": 0.2, "topic": "Gen"},
    ]
    r = client.post("/api/exam/next", params={"session_id": sid}, json={
        "theta": 0.0,
        "available_questions": questions,
        "seen_ids": [],
    })
    assert r.status_code == 200
    picked = r.json()["question"]
    assert picked["question_id"] == "H"  # closest b to theta=1.0 is 0.9


def test_telemetry_logging_called(monkeypatch):
    # Monkeypatch telemetry functions to observe calls
    import adaptive_engine.routers.exam_session as exam_router
    calls = {"exposure": [], "response": []}
    monkeypatch.setattr(exam_router, "log_exposure", lambda sid, uid, eid, qid: calls["exposure"].append((sid, uid, eid, qid)))
    monkeypatch.setattr(exam_router, "log_response", lambda sid, uid, eid, qid, ok: calls["response"].append((sid, uid, eid, qid, ok)))

    # Start session
    r = client.post("/api/exam/start", json={"user_id": 55, "exam_id": 77})
    sid = r.json()["session_id"]

    questions = [
        {"question_id": 10, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"},
        {"question_id": 11, "a": 1.0, "b": 0.5, "c": 0.2, "topic": "T"},
    ]
    # Next (logs exposure)
    r = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": []})
    q = r.json()["question"]
    assert len(calls["exposure"]) == 1
    assert calls["exposure"][0][0] == sid
    # Answer (logs response)
    r = client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q, "correct": True, "answered_items": []})
    assert len(calls["response"]) == 1


def test_stop_rule_on_se_threshold():
    # Construct answered_items with high information to drive SE down and trigger stop
    # Info sum ~ (1/threshold^2) → for threshold 0.3, need sum >= 11.12
    # We'll build 12 items with info=1
    answered_items = [{"info": 1.0} for _ in range(12)]
    question = {"question_id": 10, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Algebra"}
    r = client.post("/api/exam/answer", json={
        "theta": 0.0,
        "question": question,
        "correct": True,
        "answered_items": answered_items,
    })
    data = r.json()
    assert data["stop"] is True


def test_settings_endpoint_and_deterministic_mode():
    # Get current policy
    r = client.get("/api/settings/selection")
    assert r.status_code == 200
    cur = r.json()

    # Patch to deterministic True
    r = client.patch("/api/settings/selection", json={
        "prefer_balanced": True,
        "deterministic": True,
        "max_per_topic": None,
    })
    assert r.status_code == 200
    newp = r.json()
    assert newp["deterministic"] is True

    # With deterministic mode, repeated selection should pick the same best item
    questions = [
        {"question_id": 101, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T1"},
        {"question_id": 102, "a": 1.0, "b": 0.1, "c": 0.2, "topic": "T2"},
    ]
    payload_next = {"theta": 0.0, "available_questions": questions, "seen_ids": []}
    ids = []
    for _ in range(3):
        r = client.post("/api/exam/next", json=payload_next)
        assert r.status_code == 200
        ids.append(r.json()["question"]["question_id"])
    assert len(set(ids)) == 1


def test_settings_get_and_reset_to_env_with_namespace():
    # Reset baseline (no namespace) to env defaults and capture baseline
    client.post("/api/settings/selection/reset-to-env")
    base = client.get("/api/settings/selection").json()

    # Set namespaced policy
    ns = "exam:math"
    r = client.patch("/api/settings/selection", params={"namespace": ns}, json={
        "prefer_balanced": False,
        "deterministic": True,
        "max_per_topic": 2,
    })
    assert r.status_code == 200
    r = client.get("/api/settings/selection", params={"namespace": ns})
    pol = r.json()
    assert pol["deterministic"] is True and pol["prefer_balanced"] is False and pol["max_per_topic"] == 2

    # Reset namespaced policy to env defaults
    r = client.post("/api/settings/selection/reset-to-env", params={"namespace": ns})
    assert r.status_code == 200
    after = r.json()
    # After reset, values should equal non-namespaced env baseline
    assert after == base


def test_namespace_listing_and_hierarchical_resolution():
    # Reset global and set org-level policy
    client.post("/api/settings/selection/reset-to-env")
    org_ns = "org:univprep"
    client.patch("/api/settings/selection", params={"namespace": org_ns}, json={
        "prefer_balanced": True,
        "deterministic": True,
        "max_per_topic": 2,
    })

    # For deeper namespace org:univprep:exam1, resolved policy should inherit from org-level
    r = client.get("/api/settings", params={"namespace": f"{org_ns}:exam1"})
    eff = r.json()
    assert eff["selection_policy"]["deterministic"] is True
    assert eff["selection_policy"]["max_per_topic"] == 2

    # List namespaces should include global and org-level
    r = client.get("/api/settings/namespaces")
    data = r.json()
    assert "" in data["namespaces"]  # global
    assert org_ns in data["namespaces"]


def test_multi_level_hierarchy_and_metadata():
    # Reset all
    client.post("/api/settings/selection/reset-to-env", headers={"X-Admin-Token": ""})
    base_eff = client.get("/api/settings").json()
    assert base_eff["selection_policy_source"] in ("env", "runtime", "redis")

    # Set org-level and dept-level, but not exam-level; ensure resolution walks chain
    org = "org:alpha"
    dept = f"{org}:math"
    exam = f"{dept}:midterm"
    client.patch("/api/settings/selection", params={"namespace": org}, json={
        "prefer_balanced": True,
        "deterministic": False,
        "max_per_topic": 3,
    }, headers={"X-Admin-Token": ""})
    client.patch("/api/settings/selection", params={"namespace": dept}, json={
        "prefer_balanced": False,
        "deterministic": True,
        "max_per_topic": 2,
    }, headers={"X-Admin-Token": ""})

    eff = client.get("/api/settings", params={"namespace": exam}).json()
    assert eff["selection_policy"]["deterministic"] is True  # resolved from dept
    assert eff["selection_policy"]["max_per_topic"] == 2
    assert eff["selection_policy_source"] in ("runtime", "redis")
    assert eff.get("selection_policy_last_updated") is None or isinstance(eff.get("selection_policy_last_updated"), str)

    # Namespaces listing should include metadata entries
    r = client.get("/api/settings/namespaces").json()
    assert isinstance(r["policies"], dict)
    pmeta = r["policies"][dept]
    assert set(pmeta.keys()) == {"policy", "source", "resolved_namespace", "last_updated"}


def test_runtime_ttl_expiry_behavior():
    # Set a short TTL for runtime (env var not easily changeable here), so we simulate by setting then sleeping
    # We rely on in-memory TTL cleanup in get_selection_policy
    client.post("/api/settings/selection/reset-to-env", headers={"X-Admin-Token": ""})
    ns = "ttl:test"
    # Patch policy
    client.patch("/api/settings/selection", params={"namespace": ns}, json={
        "prefer_balanced": True,
        "deterministic": True,
        "max_per_topic": 1,
    }, headers={"X-Admin-Token": ""})
    # Direct read should show runtime/redis, not env
    eff1 = client.get("/api/settings", params={"namespace": ns}).json()
    assert eff1["selection_policy_source"] in ("runtime", "redis")
    # Force internal expiry by manually clearing runtime and verifying fallback to env works
    client.post("/api/settings/selection/reset-to-env", params={"namespace": ns}, headers={"X-Admin-Token": ""})
    eff2 = client.get("/api/settings", params={"namespace": ns}).json()
    assert eff2["selection_policy_source"] in ("env", "redis")


def test_exposure_cap_with_max_per_topic():
    # Set max_per_topic=1 and verify we alternate topics instead of repeating
    r = client.patch("/api/settings/selection", json={
        "prefer_balanced": True,
        "deterministic": True,
        "max_per_topic": 1,
    })
    assert r.status_code == 200

    questions = [
        {"question_id": "A1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Algebra"},
        {"question_id": "A2", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Algebra"},
        {"question_id": "G1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Geometry"},
        {"question_id": "G2", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "Geometry"},
    ]
    # use session to accumulate topic_counts
    sid = client.post("/api/exam/start", json={"user_id": 5, "exam_id": 505}).json()["session_id"]
    seen: list[str] = []

    # First pick should be either topic; second pick should be the other due to cap when using session state
    r1 = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": seen})
    q1 = r1.json()["question"]
    seen.append(q1["question_id"])
    # answer once to update topic_counts in session
    client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q1, "correct": True, "answered_items": []})

    r2 = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": seen})
    q2 = r2.json()["question"]
    # Must be a different topic due to max_per_topic=1
    assert q2["topic"] != q1["topic"]


def test_theta_se_plot_png_bytes():
    from adaptive_engine.utils.plotting import theta_se_curve

    thetas = [-2.0, -1.0, 0.0, 1.0, 2.0]
    ses = [0.8, 0.6, 0.4, 0.5, 0.7]
    png = theta_se_curve(thetas, ses, title="Theta-SE Curve")
    assert isinstance(png, (bytes, bytearray))
    # PNG signature check
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_reports_theta_se_png_direct_arrays():
    from adaptive_engine.main import app
    from fastapi.testclient import TestClient

    c = TestClient(app)
    r = c.get("/api/reports/theta-se.png", params=[("theta", -1), ("theta", 0), ("theta", 1), ("se", 0.7), ("se", 0.5), ("se", 0.6)])
    assert r.status_code == 200
    assert r.headers.get("content-type") == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_session_state_endpoint_and_histories(monkeypatch):
    # Monkeypatch initial theta to 0.5 for predictable seed
    import adaptive_engine.routers.exam_session as exam_router
    monkeypatch.setattr(exam_router, "get_initial_theta", lambda uid, eid: 0.5)

    # Start session
    r = client.post("/api/exam/start", json={"user_id": 9, "exam_id": 9})
    sid = r.json()["session_id"]

    # First state: theta_history should have one element (0.5)
    s = client.get("/api/exam/state", params={"session_id": sid}).json()
    assert s["theta_history"] == [0.5]
    assert s["answered_count"] == 0

    # Do one question/answer
    questions = [
        {"question_id": 100, "a": 1.0, "b": 0.4, "c": 0.2, "topic": "T"},
        {"question_id": 101, "a": 1.0, "b": 0.6, "c": 0.2, "topic": "T"},
    ]
    r = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": []})
    q = r.json()["question"]
    r = client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.5, "question": q, "correct": True, "answered_items": []})
    # State now should have histories with length 2 and 1 respectively
    s2 = client.get("/api/exam/state", params={"session_id": sid}).json()
    assert len(s2["theta_history"]) >= 2
    assert len(s2["se_history"]) >= 1


def test_finish_includes_ci_and_scaled_score_when_session():
    # Ensure finish returns theta/se/ci/scaled_score if session_id is provided
    r = client.post("/api/exam/start", json={"user_id": 7, "exam_id": 77})
    sid = r.json()["session_id"]
    # Do one cycle so we have histories
    questions = [
        {"question_id": 200, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"},
        {"question_id": 201, "a": 1.0, "b": 0.1, "c": 0.2, "topic": "T"},
    ]
    rq = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": []})
    q = rq.json()["question"]
    client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q, "correct": True, "answered_items": []})
    # Finish with session_id param
    rfin = client.post("/api/exam/finish", params={"session_id": sid}, json={
        "responses": [{"question_id": q["question_id"], "is_correct": True}],
        "questions": questions,
    })
    assert rfin.status_code == 200
    fin = rfin.json()
    assert fin["status"] == "completed"
    # Optional fields present
    assert isinstance(fin.get("theta"), (int, float))
    assert isinstance(fin.get("se"), (int, float))
    assert isinstance(fin.get("scaled_score"), (int, float))
    assert isinstance(fin.get("ci"), dict) and set(fin["ci"].keys()) == {"level", "lower", "upper"}
    # Additional fields present
    assert isinstance(fin.get("percentile"), (int, float))
    assert isinstance(fin.get("items_review"), list)
    assert isinstance(fin.get("topic_breakdown"), dict)
    assert isinstance(fin.get("recommendations"), list)


def test_estimator_settings_endpoints_toggle():
    # Read current estimator settings
    r = client.get("/api/settings/estimator")
    assert r.status_code == 200
    cur = r.json()
    # Patch estimator to map and custom priors
    r2 = client.patch("/api/settings/estimator", json={"method": "map", "prior_mean": 0.3, "prior_sd": 0.8}, headers={"X-Admin-Token": ""})
    assert r2.status_code == 200
    newv = r2.json()
    assert newv["method"].lower() == "map"
    assert abs(newv["prior_mean"] - 0.3) < 1e-6
    assert abs(newv["prior_sd"] - 0.8) < 1e-6
    # Start a new session and verify priors are applied
    r3 = client.post("/api/exam/start", json={"user_id": 88, "exam_id": 888})
    sid = r3.json()["session_id"]
    st = client.get("/api/exam/state", params={"session_id": sid}).json()
    assert st["prior"]["mean"] == 0.3
    assert st["prior"]["sd"] == 0.8


def test_scale_settings_endpoints_and_scaled_score_effect():
    # Read baseline scale
    r = client.get("/api/settings/scale")
    assert r.status_code == 200
    # Patch to SAT-like scaling
    r2 = client.patch("/api/settings/scale", json={"mean_ref": 500, "sd_ref": 100}, headers={"X-Admin-Token": ""})
    assert r2.status_code == 200
    assert r2.json()["mean_ref"] == 500
    assert r2.json()["sd_ref"] == 100

    # Run a short session and finish, then verify scaled score aligns with mean+sd*theta
    r = client.post("/api/exam/start", json={"user_id": 321, "exam_id": 654})
    sid = r.json()["session_id"]
    # Provide a question and answer to get a nontrivial theta
    questions = [{"question_id": 301, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"}]
    q = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": []}).json()["question"]
    client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q, "correct": True, "answered_items": []})
    fin = client.post("/api/exam/finish", params={"session_id": sid}, json={"responses": [{"question_id": q["question_id"], "is_correct": True}], "questions": questions}).json()
    theta = float(fin.get("theta") or 0.0)
    scaled = float(fin.get("scaled_score") or 0.0)
    expected = 500 + 100 * theta
    assert abs(scaled - expected) < 1e-6


def test_irt_updater_heuristic_uses_settings(monkeypatch):
    # Prepare a fake stats fetcher with one item
    rows = [{"question_id": "Q1", "a": 1.0, "b": 0.0, "c": 0.2, "correct_rate": 0.3}]
    def fetch():
        for r in rows:
            yield r

    # Capture persisted updates
    captured = []
    def persist(qid, a, b, c):
        captured.append((qid, a, b, c))

    import adaptive_engine.services.irt_updater as updater
    # Monkeypatch settings to control target and learning rate
    class Dummy:
        irt_update_method = "heuristic"
        irt_target_correct_rate = 0.5
        irt_learning_rate = 0.2
        irt_update_max_items_per_run = None
    monkeypatch.setattr(updater, "get_settings", lambda: Dummy())

    n = updater.run_irt_update_once(fetch_stats=fetch, persist_update=persist)
    assert n == 1
    assert len(captured) == 1
    # new_b = b - lr*(target - cr) = 0 - 0.2*(0.5-0.3) = -0.04
    assert abs(captured[0][2] - (-0.04)) < 1e-6


def test_stop_settings_endpoints_and_time_limit(monkeypatch):
    # Read current stop settings
    r = client.get("/api/settings/stop")
    assert r.status_code == 200
    cur = r.json()
    assert set(cur.keys()) == {"max_items", "time_limit_sec", "se_threshold"}

    # Patch time limit to a tiny value and ensure time-based stop triggers
    # Use empty admin token consistent with other tests
    r = client.patch("/api/settings/stop", json={"time_limit_sec": 0}, headers={"X-Admin-Token": ""})
    assert r.status_code == 200
    assert r.json()["time_limit_sec"] == 0

    # Start a session and immediately answer once; elapsed ~0 but time limit is 0 => stop must be True
    r = client.post("/api/exam/start", json={"user_id": 12, "exam_id": 34})
    sid = r.json()["session_id"]
    # Next and answer
    questions = [
        {"question_id": 1, "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T"},
        {"question_id": 2, "a": 1.0, "b": 0.2, "c": 0.2, "topic": "T"},
    ]
    rq = client.post("/api/exam/next", params={"session_id": sid}, json={"theta": 0.0, "available_questions": questions, "seen_ids": []})
    q = rq.json()["question"]
    ra = client.post("/api/exam/answer", params={"session_id": sid}, json={"theta": 0.0, "question": q, "correct": True, "answered_items": []})
    data = ra.json()
    assert data["stop"] is True

    # Also verify state endpoint surfaces elapsed and remaining
    st = client.get("/api/exam/state", params={"session_id": sid}).json()
    assert "elapsed_time_sec" in st and "remaining_time_sec" in st
