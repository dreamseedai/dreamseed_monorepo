import os
from fastapi.testclient import TestClient

# Ensure LOCAL_DEV to bypass auth for tests
os.environ.setdefault("LOCAL_DEV", "true")

from apps.seedtest_api.app.main import app


def test_questions_crud_smoke():
    client = TestClient(app)

    # List (seeded)
    r = client.get("/api/seedtest/questions")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data and isinstance(data["results"], list)
    n0 = data["total"]

    # Create
    payload = {
        "stem": "테스트 문항. 다음 중 옳은 것을 고르시오.",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "difficulty": "medium",
        "topic": "대수",
        "tags": ["기초"],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201), r.text
    q = r.json()
    qid = q["id"]
    assert q["stem"].startswith("테스트 문항")

    # Get
    r = client.get(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 200
    q2 = r.json()
    assert q2["id"] == qid

    # Update
    payload["stem"] = "수정된 문항"
    payload["answer"] = 2
    r = client.put(f"/api/seedtest/questions/{qid}", json=payload)
    assert r.status_code == 200
    q3 = r.json()
    assert q3["stem"] == "수정된 문항"

    # List with filter
    r = client.get("/api/seedtest/questions", params={"q": "수정된"})
    assert r.status_code == 200
    data2 = r.json()
    assert data2["total"] >= 1

    # Delete
    r = client.delete(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # Confirm deletion
    r = client.get(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 404
