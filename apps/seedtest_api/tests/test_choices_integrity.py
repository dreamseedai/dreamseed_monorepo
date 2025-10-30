import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


pytestmark = pytest.mark.db


def _is_postgres(engine) -> bool:
    try:
        return (engine.dialect.name == "postgresql")
    except Exception:
        return False


def _has_table(engine, name: str) -> bool:
    try:
        insp = inspect(engine)
        return insp.has_table(name)
    except Exception:
        return False


def test_unique_correct_choice_enforced_when_postgres(monkeypatch):
    # Require DATABASE_URL to be configured
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")
    # Only run on Postgres with migrations applied
    from apps.seedtest_api.services import db as db_service
    engine = db_service.get_engine()
    if not _is_postgres(engine):
        pytest.skip("Postgres required for partial unique index test")

    if not _has_table(engine, "question_choices"):
        pytest.skip("question_choices table not present (migrations not applied)")

    # Ensure questions table exists too
    if not _has_table(engine, "questions"):
        pytest.skip("questions table not present")

    qid = "q-uniq-1"
    with engine.begin() as conn:
        # Insert a minimal question row if absent
        conn.execute(text(
            """
            INSERT INTO questions (id, org_id, title, stem, explanation, options, answer, difficulty, topic, tags, status, author)
            VALUES (:id, NULL, NULL, 'tmp', NULL, '[]'::jsonb, 0, 'easy', NULL, '[]'::jsonb, 'draft', 't')
            ON CONFLICT (id) DO NOTHING
            """
        ), {"id": qid})
        # Insert first correct choice
        conn.execute(text(
            """
            INSERT INTO question_choices (question_id, sort_order, content, is_correct)
            VALUES (:qid, 0, 'A', true)
            """
        ), {"qid": qid})
        # Second correct should fail due to partial unique index
        with pytest.raises(IntegrityError):
            conn.execute(text(
                """
                INSERT INTO question_choices (question_id, sort_order, content, is_correct)
                VALUES (:qid, 1, 'B', true)
                """
            ), {"qid": qid})


def test_api_writes_choices_when_enabled(monkeypatch, tmp_path):
    # Require DATABASE_URL to be configured
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")
    # Use LOCAL_DEV and the configured DATABASE_URL (CI should point to Postgres)
    monkeypatch.setenv("LOCAL_DEV", "true")
    # Ensure choices-table wiring is on
    monkeypatch.setenv("USE_CHOICES_TABLE", "true")

    from apps.seedtest_api.services import db as db_service
    engine = db_service.get_engine()
    if not _has_table(engine, "question_choices") or not _has_table(engine, "questions"):
        pytest.skip("Required tables not present; skipping choices wiring test")

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    payload = {
        "stem": "Choices wiring test",
        "options": ["A", "B", "C"],
        "answer": 1,
        "difficulty": "easy",
        "topic": "대수",
        "tags": [],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload)
    assert r.status_code in (200, 201), r.text
    q = r.json()
    qid = q["id"]

    # Verify rows in question_choices
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT sort_order, content, is_correct FROM question_choices WHERE question_id = :qid ORDER BY sort_order"), {"qid": qid}).fetchall()
    assert len(rows) == 3
    correct = [r for r in rows if r[2] is True]
    assert len(correct) == 1
    assert correct[0][0] == 1  # sort_order of correct is 1


def test_migration_backfill_sql_populates_choices(monkeypatch):
    """
    Verify that the migration backfill SQL correctly inserts rows into question_choices
    from the questions.options/answer columns.

    This mirrors the SQL used in Alembic migration 20251025_1500_question_choices.
    """
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping DB-dependent test")

    from apps.seedtest_api.services import db as db_service
    engine = db_service.get_engine()
    if not _is_postgres(engine):
        pytest.skip("Postgres required for backfill SQL test")
    if not (_has_table(engine, "questions") and _has_table(engine, "question_choices")):
        pytest.skip("Required tables not present; ensure Alembic migrations applied")

    qid = "q-backfill-1"
    # Clean slate for this question
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM question_choices WHERE question_id = :qid"), {"qid": qid})
        conn.execute(
            text(
                """
                INSERT INTO questions (id, org_id, title, stem, explanation, options, answer, difficulty, topic, tags, status, author)
                VALUES (:id, NULL, NULL, 'backfill-stem', NULL, :opts::jsonb, :ans, 'easy', NULL, '[]'::jsonb, 'draft', 't')
                ON CONFLICT (id) DO UPDATE SET options = EXCLUDED.options, answer = EXCLUDED.answer
                """
            ),
            {"id": qid, "opts": '["A","B","C"]', "ans": 2},
        )

        # Run the same backfill SQL as the migration (idempotent)
        conn.execute(
            text(
                """
                INSERT INTO question_choices (question_id, sort_order, content, is_correct)
                SELECT q.id AS question_id,
                       (t.ord - 1)::smallint AS sort_order,
                       t.elem AS content,
                       CASE WHEN q.answer = (t.ord - 1) THEN true ELSE false END AS is_correct
                FROM (
                    SELECT id, answer, options FROM questions
                    WHERE id = :qid AND options IS NOT NULL
                ) AS q,
                LATERAL json_array_elements_text(q.options) WITH ORDINALITY AS t(elem, ord)
                ON CONFLICT (question_id, sort_order) DO NOTHING
                """
            ),
            {"qid": qid},
        )

        rows = conn.execute(
            text("SELECT sort_order, content, is_correct FROM question_choices WHERE question_id = :qid ORDER BY sort_order"),
            {"qid": qid},
        ).fetchall()

    assert len(rows) == 3
    # sort_order: 0:'A', 1:'B', 2:'C'; answer=2 means index 2 is correct
    assert rows[0][0] == 0 and rows[0][1] == 'A' and rows[0][2] is False
    assert rows[1][0] == 1 and rows[1][1] == 'B' and rows[1][2] is False
    assert rows[2][0] == 2 and rows[2][1] == 'C' and rows[2][2] is True
