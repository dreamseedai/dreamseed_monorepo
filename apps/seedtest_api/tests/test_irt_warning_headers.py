import os
from fastapi.testclient import TestClient

# Ensure LOCAL_DEV to bypass auth for these header tests
os.environ.setdefault("LOCAL_DEV", "true")

from apps.seedtest_api.app.main import app


client = TestClient(app)


def test_create_emits_warning_headers_when_irt_out_of_range():
    # discrimination too low (<0.5) and guessing too high (>0.35) to trigger warnings
    payload = {
        "stem": "IRT header test create",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "difficulty": "medium",
        "topic": "대수",
        "tags": ["hdr"],
        "status": "draft",
        "discrimination": 0.2,
        "guessing": 0.4,
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201), r.text
    w = r.headers.get("Warning", "")
    xw = r.headers.get("X-Warning", "")
    # Either/both headers may be set; assert content mentions expected messages
    combo = f"{w}; {xw}".lower()
    assert "discrimination" in combo or "guessing" in combo


def test_update_emits_warning_headers_when_irt_out_of_range():
    # create baseline
    payload = {
        "stem": "IRT header test update",
        "options": ["A", "B", "C"],
        "answer": 0,
        "difficulty": "easy",
        "topic": "기하",
        "tags": ["hdr"],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201)
    qid = r.json()["id"]

    # update with out-of-range values
    upd = {
        "stem": "IRT header test update (out-of-range)",
        "options": ["A", "B", "C"],
        "answer": 2,
        "difficulty": "hard",
        "topic": "기하",
        "tags": ["hdr"],
        "status": "draft",
        "discrimination": 0.1,  # too low
        "guessing": 0.5,        # too high
    }
    r2 = client.put(f"/api/seedtest/questions/{qid}", json=upd)
    assert r2.status_code == 200, r2.text
    w = r2.headers.get("Warning", "")
    xw = r2.headers.get("X-Warning", "")
    combo = f"{w}; {xw}".lower()
    assert "discrimination" in combo or "guessing" in combo
