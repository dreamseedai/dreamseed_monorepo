#!/usr/bin/env python3
"""
MySQL -> PostgreSQL migration for tbl_question (~18.9k rows)

- Reads from MySQL using legacy mpcstudy fields (que_*)
- Normalizes each row via the project's legacy_mpc_adapter._map_legacy_item so the shape
  matches our Question contract
- Upserts into public.questions (ON CONFLICT (id) DO UPDATE) so it's safe to re-run

Usage
- Ensure apps/seedtest_api/.env has:
    MPC_MYSQL_URL=mysql+pymysql://user:pass@127.0.0.1:3306/mpcstudy_db?charset=utf8mb4
    DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1:5432/dreamseed
- Optional overrides:
    MYSQL_DSN=...  PG_DSN=...  CHUNK=2000  LOG_EVERY=1000
- Run:
    PYTHONPATH=apps python apps/seedtest_api/scripts/migrate_mysql_to_pg.py

Notes
- Creates the questions table if it does not exist (schema aligned to models.QuestionRow)
- Converts legacy timestamps to timestamptz; fills defaults for required fields
- Requires: SQLAlchemy, PyMySQL, psycopg2-binary, python-dotenv
"""
from __future__ import annotations

import os
import sys
import math
import json
from typing import Any, Dict, Iterable, List, Tuple
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from psycopg2.extras import execute_values
import psycopg2

try:
    # Load env from project .env files for convenience
    from dotenv import load_dotenv
    # Prefer app-level .env, then root .env
    app_env = Path(__file__).resolve().parents[1] / ".env"
    root_env = Path(__file__).resolve().parents[3] / ".env"
    for env_path in [app_env, root_env]:
        if env_path.exists():
            load_dotenv(str(env_path), override=False)
except Exception:
    pass

# Ensure project root on sys.path so we can import adapter without requiring PYTHONPATH externally
PROJ_ROOT = Path(__file__).resolve().parents[3]
if str(PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJ_ROOT))

# Import the same mapping used by the API's legacy adapter for consistency
from apps.seedtest_api.services.legacy_mpc_adapter import _map_legacy_item  # type: ignore

# DSNs with sensible defaults from app settings
MYSQL_DSN = os.getenv(
    "MYSQL_DSN",
    os.getenv(
        "MPC_MYSQL_URL",
        "mysql+pymysql://mpcstudy_root:2B3Z45J3DACT@127.0.0.1:3306/mpcstudy_db?charset=utf8mb4",
    ),
)
PG_DSN = os.getenv(
    "PG_DSN",
    os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/dreamseed"),
)
CHUNK = int(os.getenv("CHUNK", "2000"))
LOG_EVERY = int(os.getenv("LOG_EVERY", "2000"))
DRY_RUN = os.getenv("DRY_RUN", "0").lower() in {"1", "true", "yes"}

# Columns we need from MySQL (aligned with adapter expectations)
SELECT_SQL = """
SELECT
  que_id             AS id,
  que_en_title       AS que_en_title,
  que_en_desc        AS que_en_desc,
  que_en_solution    AS que_en_solution,
  que_en_answers     AS que_en_answers,
  que_en_answerm     AS que_en_answerm,
  que_class          AS que_class,
  que_grade          AS que_grade,
  que_level          AS que_level,
  que_createddate    AS created_at,
  que_modifieddate   AS updated_at
FROM tbl_question
ORDER BY que_id
LIMIT :limit OFFSET :offset
"""

COUNT_SQL = "SELECT COUNT(*) FROM tbl_question"

# Target DDL (close to models.QuestionRow)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.questions (
  id            text PRIMARY KEY,
  org_id        integer NULL,
  title         text NULL,
  stem          text NOT NULL,
  explanation   text NULL,
  options       jsonb NOT NULL,
  answer        integer NOT NULL,
  difficulty    text NOT NULL,
  topic         text NULL,
  topic_id      bigint NULL,
  tags          jsonb NULL,
  status        text NOT NULL,
  author        text NULL,
  created_by    text NULL,
  updated_by    text NULL,
  discrimination double precision NULL,
  guessing      double precision NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
)
"""

UPSERT_SQL = """
INSERT INTO public.questions (
  id, org_id, title, stem, explanation, options, answer, difficulty, topic, topic_id, tags, status,
  author, created_by, updated_by, discrimination, guessing, created_at, updated_at
) VALUES %s
ON CONFLICT (id) DO UPDATE SET
  org_id = EXCLUDED.org_id,
  title = EXCLUDED.title,
  stem = EXCLUDED.stem,
  explanation = EXCLUDED.explanation,
  options = EXCLUDED.options,
  answer = EXCLUDED.answer,
  difficulty = EXCLUDED.difficulty,
  topic = EXCLUDED.topic,
  topic_id = EXCLUDED.topic_id,
  tags = EXCLUDED.tags,
  status = EXCLUDED.status,
  author = EXCLUDED.author,
  created_by = COALESCE(EXCLUDED.created_by, public.questions.created_by),
  updated_by = COALESCE(EXCLUDED.updated_by, public.questions.updated_by),
  discrimination = EXCLUDED.discrimination,
  guessing = EXCLUDED.guessing,
  created_at = LEAST(public.questions.created_at, EXCLUDED.created_at),
  updated_at = GREATEST(public.questions.updated_at, EXCLUDED.updated_at)
"""


def _dt(ts: Any) -> datetime:
    """Convert adapter's timestamp (epoch float or ISO string) to aware datetime."""
    if ts is None:
        return datetime.now(timezone.utc)
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    try:
        s = str(ts)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.now(timezone.utc)


def _pg_raw_conn(engine: Engine):
    return engine.raw_connection()


def _as_values(items: Iterable[Dict[str, Any]]) -> List[Tuple[Any, ...]]:
    vals: List[Tuple[Any, ...]] = []
    for it in items:
        # Ensure defaults for required fields
        options = it.get("options") or ["A", "B", "C", "D"]
        if not isinstance(options, list):
            # try to coerce
            try:
                options = json.loads(options)
            except Exception:
                options = ["A", "B", "C", "D"]
        tags = it.get("tags")
        # psycopg2 will adapt lists/dicts into json when using Json adapter, but execute_values
        # can take native python and cast. We'll send via psycopg2.extras.Json on cursor execution.
        vals.append(
            (
                str(it.get("id") or ""),
                it.get("org_id"),
                it.get("title"),
                it.get("stem") or "",
                it.get("explanation"),
                options,  # adapt to jsonb
                int(it.get("answer") or 0),
                it.get("difficulty") or "medium",
                it.get("topic"),
                it.get("topic_id"),
                tags if tags is not None else None,  # adapt to jsonb
                it.get("status") or "published",
                it.get("author"),
                it.get("created_by"),
                it.get("updated_by"),
                it.get("discrimination"),
                it.get("guessing"),
                _dt(it.get("created_at")),
                _dt(it.get("updated_at")),
            )
        )
    return vals


def main() -> None:
    print("[migrate] Using MySQL:", MYSQL_DSN)
    print("[migrate] Using Postgres:", PG_DSN)

    mysql = create_engine(MYSQL_DSN, pool_pre_ping=True, future=True)
    pg = create_engine(PG_DSN, pool_pre_ping=True, future=True)

    # Count source
    with mysql.connect() as mcon:
        total = mcon.execute(text(COUNT_SQL)).scalar_one()
        print(f"[migrate] Source tbl_question count = {total}")

    # Ensure target table exists
    with pg.connect() as pcon:
        pcon.execute(text(CREATE_TABLE_SQL))
        pcon.commit()

    if DRY_RUN:
        print("[migrate] DRY_RUN=1 set. Skipping data upsert after validating connections and table.")
        return

    pages = int(math.ceil(total / CHUNK)) if total else 0
    inserted = 0

    with mysql.connect() as mcon:
        pgraw = _pg_raw_conn(pg)
        cur = None
        try:
            cur = pgraw.cursor()
            # Use JSON adapter for options/tags
            from psycopg2.extras import Json as PGJson

            for p in range(pages):
                offset = p * CHUNK
                rows = mcon.execute(text(SELECT_SQL), {"limit": CHUNK, "offset": offset}).mappings().all()
                if not rows:
                    break
                mapped = [_map_legacy_item(dict(r)) for r in rows]
                # Coerce id to non-empty strings using original que_id if needed
                for i, r in enumerate(rows):
                    if not mapped[i].get("id"):
                        mapped[i]["id"] = str(r.get("id"))
                values = _as_values(mapped)
                # Wrap JSON columns
                values = [
                    (
                        v[0], v[1], v[2], v[3], v[4], PGJson(v[5], dumps=json.dumps), v[6], v[7], v[8], v[9],
                        PGJson(v[10], dumps=json.dumps) if v[10] is not None else None, v[11], v[12], v[13], v[14], v[15], v[16], v[17], v[18]
                    ) for v in values
                ]
                execute_values(cur, UPSERT_SQL, values, page_size=min(CHUNK, 1000))
                pgraw.commit()
                inserted += len(values)
                if inserted % LOG_EVERY == 0 or p == pages - 1:
                    print(f"[migrate] Upserted {inserted}/{total} rows...")
        finally:
            try:
                if cur is not None:
                    cur.close()
            except Exception:
                pass
            try:
                pgraw.close()
            except Exception:
                pass

    print("[migrate] Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[migrate] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print("[migrate] ERROR:", repr(e))
        raise
