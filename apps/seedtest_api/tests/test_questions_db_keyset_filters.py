import os
from fastapi.testclient import TestClient


def make_sqlite_url(tmp_path):
    return f"sqlite+pysqlite:///{tmp_path}/seedtest_kf.db?check_same_thread=False"


def setup_db(tmp_path):
    os.environ["DATABASE_URL"] = make_sqlite_url(tmp_path)
    os.environ["LOCAL_DEV"] = "true"
    from apps.seedtest_api.services import db as db_service
    from apps.seedtest_api.db.base import Base
    from apps.seedtest_api.models.question import QuestionRow
    engine = db_service.get_engine()
    Base.metadata.create_all(engine, tables=[QuestionRow.__table__])


def test_keyset_pagination_and_filters(tmp_path):
    setup_db(tmp_path)
    from apps.seedtest_api.app.main import app

    client = TestClient(app)

    # Seed 5 questions with different attributes
    seeds = [
        {"stem": "Algebra basics 1", "topic": "대수", "difficulty": "easy", "status": "published"},
        {"stem": "Geometry intro 2", "topic": "기하", "difficulty": "medium", "status": "draft"},
        {"stem": "Probability 3", "topic": "확률", "difficulty": "hard", "status": "draft"},
        {"stem": "Algebra advanced 4", "topic": "대수", "difficulty": "medium", "status": "published"},
        {"stem": "Geometry advanced 5", "topic": "기하", "difficulty": "easy", "status": "published"},
    ]
    for s in seeds:
        payload = {
            "stem": s["stem"],
            "options": ["A", "B", "C", "D"],
            "answer": 1,
            "difficulty": s["difficulty"],
            "topic": s["topic"],
            "tags": ["tag"],
            "status": s["status"],
        }
        r = client.post("/api/seedtest/questions", json=payload)
        assert r.status_code in (200, 201)

    # Keyset pagination over updated_at desc with limit=2
    r1 = client.get("/api/seedtest/questions", params={"limit": 2, "sort_by": "updated_at", "order": "desc"})
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    p1 = d1["results"]
    cursor = d1.get("next_cursor_opaque")
    assert len(p1) == 2
    assert cursor, "Expected next_cursor for keyset"

    r2 = client.get("/api/seedtest/questions", params={"limit": 2, "sort_by": "updated_at", "order": "desc", "cursor": cursor})
    assert r2.status_code == 200
    d2 = r2.json()
    p2 = d2["results"]
    # No overlap with first page
    ids1 = {x["id"] for x in p1}
    ids2 = {x["id"] for x in p2}
    assert not (ids1 & ids2)

    # Third page (may be 1 item)
    cursor2 = d2.get("next_cursor_opaque")
    if cursor2:
        r3 = client.get("/api/seedtest/questions", params={"limit": 2, "sort_by": "updated_at", "order": "desc", "cursor": cursor2})
        assert r3.status_code == 200
        d3 = r3.json()
        p3 = d3["results"]
        ids3 = {x["id"] for x in p3}
        assert not (ids1 & ids3) and not (ids2 & ids3)
        # Combined should equal total
        total_ids = ids1 | ids2 | ids3
        assert len(total_ids) == d3["total"]
    else:
        # Two pages cover all results
        total_ids = ids1 | ids2
        assert len(total_ids) == d2["total"]

    # Filters: q (stem), topic, difficulty, status
    r = client.get("/api/seedtest/questions", params={"q": "algebra"})
    assert r.status_code == 200
    names = [x["stem"].lower() for x in r.json()["results"]]
    assert any("algebra" in n for n in names)

    r = client.get("/api/seedtest/questions", params={"topic": "대수"})
    assert r.status_code == 200
    assert all(x.get("topic") == "대수" for x in r.json()["results"])

    r = client.get("/api/seedtest/questions", params={"difficulty": "medium"})
    assert r.status_code == 200
    assert all(x.get("difficulty") == "medium" for x in r.json()["results"])

    r = client.get("/api/seedtest/questions", params={"status": "published"})
    assert r.status_code == 200
    assert all(x.get("status") == "published" for x in r.json()["results"])

    # Sorting columns: topic, difficulty, status, created_at asc
    r = client.get("/api/seedtest/questions", params={"sort_by": "topic", "order": "asc"})
    assert r.status_code == 200

    r = client.get("/api/seedtest/questions", params={"sort_by": "difficulty", "order": "asc"})
    assert r.status_code == 200

    r = client.get("/api/seedtest/questions", params={"sort_by": "status", "order": "asc"})
    assert r.status_code == 200

    r = client.get("/api/seedtest/questions", params={"sort_by": "created_at", "order": "asc"})
    assert r.status_code == 200
