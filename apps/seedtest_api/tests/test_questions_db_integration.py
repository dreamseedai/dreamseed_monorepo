import os
import tempfile
import importlib
from fastapi.testclient import TestClient


def make_sqlite_url(tmpdir: str) -> str:
    return f"sqlite+pysqlite:///{tmpdir}/seedtest.db?check_same_thread=False"


def test_questions_db_crud_sqlite(tmp_path):
    # Set env BEFORE importing app
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    os.environ["DATABASE_URL"] = make_sqlite_url(str(db_dir))
    os.environ["LOCAL_DEV"] = "true"  # bypass JWT

    # Import after env is set
    from apps.seedtest_api.services import db as db_service
    from apps.seedtest_api.db.base import Base
    from apps.seedtest_api.models.question import QuestionRow

    # Initialize engine and create tables
    engine = db_service.get_engine()
    Base.metadata.create_all(engine, tables=[QuestionRow.__table__])

    # Import app now
    from apps.seedtest_api.app.main import app

    client = TestClient(app)

    # Verify empty list
    r = client.get("/api/seedtest/questions")
    assert r.status_code == 200
    data0 = r.json()
    assert data0["total"] == 0

    # Create
    payload = {
        "stem": "DB 문항 1",
        "options": ["A", "B", "C", "D"],
        "answer": 2,
        "difficulty": "easy",
        "topic": "확률",
        "tags": ["기초"],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201), r.text
    q = r.json()
    qid = q["id"]

    # Get
    r = client.get(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 200
    assert r.json()["stem"] == "DB 문항 1"

    # Update
    payload["stem"] = "DB 문항 1 - 수정"
    payload["answer"] = 3
    r = client.put(f"/api/seedtest/questions/{qid}", json=payload)
    assert r.status_code == 200
    assert r.json()["stem"] == "DB 문항 1 - 수정"

    # Topics should include '확률'
    r = client.get("/api/seedtest/questions/topics")
    assert r.status_code == 200
    topics = r.json()
    assert "확률" in topics

    # Delete (soft)
    r = client.delete(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # GET by id should 404
    r = client.get(f"/api/seedtest/questions/{qid}")
    assert r.status_code == 404

    # Topics should exclude deleted-only topics (now empty)
    r = client.get("/api/seedtest/questions/topics")
    assert r.status_code == 200
    topics2 = r.json()
    assert "확률" not in topics2
