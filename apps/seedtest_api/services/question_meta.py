"""Utilities for managing question.meta JSONB IRT parameters and tags."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def update_irt_params(
    session: Session,
    question_id: int,
    *,
    a: float | None = None,
    b: float | None = None,
    c: float | None = None,
    model: str = "2PL",
    version: str | None = None,
) -> None:
    """Update IRT parameters in question.meta JSONB.

    Args:
        session: Database session
        question_id: Question ID
        a: Discrimination parameter
        b: Difficulty parameter
        c: Guessing parameter (for 3PL, optional)
        model: IRT model ("2PL", "3PL", "Rasch")
        version: Pipeline/run version (optional)
    """
    # Load existing meta
    result = session.execute(
        text("SELECT meta FROM question WHERE id = :question_id"),
        {"question_id": question_id},
    )
    row = result.fetchone()

    if row is None:
        raise ValueError(f"Question {question_id} not found")

    current_meta = dict(row[0]) if row[0] else {}
    irt_data = current_meta.get("irt", {})

    # Update IRT parameters
    if a is not None:
        irt_data["a"] = a
    if b is not None:
        irt_data["b"] = b
    if c is not None:
        irt_data["c"] = c
    if model:
        irt_data["model"] = model
    if version:
        irt_data["version"] = version

    current_meta["irt"] = irt_data

    # Update meta
    session.execute(
        text(
            """
            UPDATE question
            SET meta = :meta_json::jsonb
            WHERE id = :question_id
        """
        ),
        {
            "question_id": question_id,
            "meta_json": json.dumps(current_meta),
        },
    )
    session.commit()


def add_tags(
    session: Session,
    question_id: int,
    tags: list[str],
    *,
    replace: bool = False,
) -> None:
    """Add tags to question.meta JSONB.

    Args:
        session: Database session
        question_id: Question ID
        tags: List of tag strings
        replace: If True, replace existing tags; otherwise merge
    """
    result = session.execute(
        text("SELECT meta FROM question WHERE id = :question_id"),
        {"question_id": question_id},
    )
    row = result.fetchone()

    if row is None:
        raise ValueError(f"Question {question_id} not found")

    current_meta = dict(row[0]) if row[0] else {}

    if replace:
        current_meta["tags"] = tags
    else:
        existing_tags = set(current_meta.get("tags", []))
        existing_tags.update(tags)
        current_meta["tags"] = sorted(existing_tags)

    session.execute(
        text(
            """
            UPDATE question
            SET meta = :meta_json::jsonb
            WHERE id = :question_id
        """
        ),
        {
            "question_id": question_id,
            "meta_json": json.dumps(current_meta),
        },
    )
    session.commit()


def get_irt_params(
    session: Session,
    question_id: int,
) -> dict[str, Any] | None:
    """Get IRT parameters from question.meta JSONB.

    Returns:
        Dictionary with keys: a, b, c (optional), model, version (optional)
        Returns None if question not found or no IRT data
    """
    result = session.execute(
        text(
            """
            SELECT 
              (meta->'irt'->>'a')::float AS a,
              (meta->'irt'->>'b')::float AS b,
              (meta->'irt'->>'c')::float AS c,
              meta->'irt'->>'model' AS model,
              meta->'irt'->>'version' AS version
            FROM question
            WHERE id = :question_id
        """
        ),
        {"question_id": question_id},
    )
    row = result.fetchone()

    if row is None:
        return None

    if row[0] is None:  # No IRT data
        return None

    params = {
        "a": float(row[0]),
        "b": float(row[1]),
        "model": row[3] or "2PL",
    }

    if row[2] is not None:  # c parameter exists
        params["c"] = float(row[2])

    if row[4]:
        params["version"] = row[4]

    return params


def list_questions_by_tags(
    session: Session,
    tags: list[str],
    *,
    require_all: bool = False,
) -> list[int]:
    """List question IDs that match given tags.

    Args:
        session: Database session
        tags: List of tag strings to search for
        require_all: If True, question must have all tags; otherwise any tag

    Returns:
        List of question IDs
    """
    if require_all:
        # All tags must be present
        query = "SELECT id FROM question WHERE meta @> :tags_json::jsonb"
        tags_json = json.dumps({"tags": tags})
    else:
        # Any tag matches
        query = """
            SELECT id FROM question
            WHERE EXISTS (
              SELECT 1 FROM jsonb_array_elements_text(meta->'tags') AS tag
              WHERE tag = ANY(:tags_array::text[])
            )
        """
        tags_array = tags

    result = session.execute(
        text(query),
        {
            "tags_json": tags_json if require_all else None,
            "tags_array": tags_array if not require_all else None,
        },
    )

    return [row[0] for row in result.fetchall()]
