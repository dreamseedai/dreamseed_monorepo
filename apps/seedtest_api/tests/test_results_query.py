import os

import pytest

# Skip if no DB configured
if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL not set; skipping DB-backed results listing tests",
        allow_module_level=True,
    )

from seedtest_api.services.result_query import list_results_by_user_exam  # noqa: E402
from seedtest_api.services.result_service import upsert_result  # noqa: E402


def test_list_results_filters_and_paging(monkeypatch):
    # Insert a few sample rows via upsert (let DB manage UUID PK)
    upsert_result(
        "sess_A",
        {"score": {"raw": 1, "scaled": 10}},
        1,
        10,
        user_id="11111111-1111-1111-1111-111111111111",
        exam_id=101,
    )
    upsert_result(
        "sess_B",
        {"score": {"raw": 2, "scaled": 20}},
        2,
        20,
        user_id="11111111-1111-1111-1111-111111111111",
        exam_id=102,
    )
    upsert_result(
        "sess_C",
        {"score": {"raw": 3, "scaled": 30}},
        3,
        30,
        user_id="22222222-2222-2222-2222-222222222222",
        exam_id=101,
    )

    rows_user = list_results_by_user_exam(
        user_id="11111111-1111-1111-1111-111111111111"
    )
    assert all(
        r["user_id"] == "11111111-1111-1111-1111-111111111111" for r in rows_user
    )

    rows_exam = list_results_by_user_exam(exam_id=101)
    assert all(r["exam_id"] == 101 for r in rows_exam)

    rows_both = list_results_by_user_exam(
        user_id="11111111-1111-1111-1111-111111111111", exam_id=101
    )
    assert all(
        r["user_id"] == "11111111-1111-1111-1111-111111111111" and r["exam_id"] == 101
        for r in rows_both
    )

    # basic paging smoke test
    first_page = list_results_by_user_exam(limit=1)
    assert len(first_page) <= 1
