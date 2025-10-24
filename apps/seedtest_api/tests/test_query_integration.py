import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text

from alembic import command

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "apps" / "seedtest_api"

# Gate integration tests behind RUN_INTEGRATION_TESTS env flag
# Set RUN_INTEGRATION_TESTS=1 to enable (CI sets it by default)
SKIP_INTEGRATION = not os.getenv("RUN_INTEGRATION_TESTS", os.getenv("CI", "")).strip()
pytestmark = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Integration tests disabled (set RUN_INTEGRATION_TESTS=1 to enable)",
)


def _wait_port(host: str, port: int, timeout: float = 60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(1)
            try:
                s.connect((host, port))
                return
            except OSError:
                time.sleep(0.5)
    raise RuntimeError("DB port did not open in time")


def _compose_up():
    subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "docker-compose.db.yml"), "up", "-d"],
        check=True,
    )
    _wait_port("127.0.0.1", 5432, 60)


def _compose_down():
    subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "docker-compose.db.yml"), "down", "-v"],
        check=False,
    )


def _alembic_upgrade(tags_kind: str):
    os.environ["DATABASE_URL"] = (
        "postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed_db"
    )
    os.environ["ALEMBIC_SEED"] = "true"  # optional seed
    os.environ["ALEMBIC_TAGS_KIND"] = tags_kind
    cfg = Config(str(APP / "alembic.ini"))
    command.upgrade(cfg, "head")


def _insert_sample_data_text_array():
    from apps.seedtest_api.services.db import get_session

    with get_session() as s:
        # Ensure topics exist (seed likely added at least one); otherwise insert minimal
        s.execute(
            text(
                """
    INSERT INTO topics (topic_id, name) VALUES (100, 'Algebra')
    ON CONFLICT (topic_id) DO NOTHING;
    """
            )
        )
        # Two questions with different tags
        s.execute(
            text(
                """
    INSERT INTO questions (content, topic_id, difficulty, tags)
    VALUES (:c1, 100, 0.1, :t1::text[]), (:c2, 100, 0.2, :t2::text[]);
    """
            ),
            {
                "c1": "Algebra basics",
                "t1": ["algebra", "geometry"],
                "c2": "Reading comprehension",
                "t2": ["reading"],
            },
        )


def _insert_sample_data_jsonb():
    from apps.seedtest_api.services.db import get_session

    with get_session() as s:
        s.execute(
            text(
                """
    INSERT INTO topics (topic_id, name) VALUES (200, 'Geometry')
    ON CONFLICT (topic_id) DO NOTHING;
    """
            )
        )
        s.execute(
            text(
                """
    INSERT INTO questions (content, topic_id, difficulty, tags)
    VALUES (:c1, 200, 0.1, to_jsonb(:t1::text[])), (:c2, 200, 0.2, to_jsonb(:t2::text[]));
    """
            ),
            {
                "c1": "Geometry basics",
                "t1": ["algebra", "geometry"],
                "c2": "Reading comp",
                "t2": ["reading"],
            },
        )


@pytest.mark.integration
def test_query_text_array_end_to_end():
    _compose_up()
    try:
        _alembic_upgrade("text[]")
        _insert_sample_data_text_array()

        from apps.seedtest_api.services.loader import build_loader_filters
        from apps.seedtest_api.services.query import execute_questions_query

        # Filters: match tags any of ['algebra','proof']
        os.environ["BANK_TAGS"] = "algebra proof"
        os.environ["BANK_TOPIC_IDS"] = ""  # not used here
        filters = build_loader_filters()
        rows = execute_questions_query(filters, limit=10)
        titles = [r["content"] for r in rows]
        assert any("Algebra" in t for t in titles)
        assert all(t in ("Algebra basics", "Reading comprehension") for t in titles)
    finally:
        _compose_down()


@pytest.mark.integration
def test_query_jsonb_end_to_end():
    _compose_up()
    try:
        _alembic_upgrade("jsonb")
        _insert_sample_data_jsonb()

        from apps.seedtest_api.services.loader import build_loader_filters
        from apps.seedtest_api.services.query import execute_questions_query

        os.environ["BANK_TAGS"] = "algebra proof"
        filters = build_loader_filters()
        rows = execute_questions_query(filters, limit=10)
        titles = [r["content"] for r in rows]
        assert any("Geometry" in t for t in titles)
        assert all(t in ("Geometry basics", "Reading comp") for t in titles)
    finally:
        _compose_down()
