import sys
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

from fastapi.testclient import TestClient  # type: ignore
from seedtest_api.main import app  # noqa: E402
from seedtest_api.services import result_service  # noqa: E402
from seedtest_api import deps as deps_mod  # noqa: E402
from seedtest_api.security import jwt as jwt_mod  # noqa: E402

client = TestClient(app)


def test_student_forbidden_on_other_users_session(monkeypatch):
    # Use strict mode (no LOCAL_DEV bypass) only within this test
    monkeypatch.setenv("LOCAL_DEV", "false")
    # Token for user-1 (student)
    async def fake_decode(_token: str):
        return {"sub": "user-1", "roles": ["student"], "org_id": 1, "scope": "exam:read"}

    # Patch both the security.jwt.decode_token and deps.decode_token (direct import)
    monkeypatch.setattr(jwt_mod, "decode_token", fake_decode)
    monkeypatch.setattr(deps_mod, "decode_token", fake_decode)

    # Active session state owned by user-2
    def fake_state(_sid: str):
        return {"user_id": "user-2", "responses": [{"correct": True}]}

    monkeypatch.setattr(result_service, "get_session_state", fake_state)

    # Call create/refresh endpoint with Authorization header; expect 403
    r = client.post(
        "/api/seedtest/exams/sess-owned-by-user-2/result",
        headers={"Authorization": "Bearer dummy"},
        json={"force": False},
    )
    assert r.status_code == 403, r.text
