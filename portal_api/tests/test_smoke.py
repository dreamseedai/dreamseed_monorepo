import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/dreamseed")

import app.main as appmod  # noqa: E402


@pytest.mark.asyncio
async def test_ok_and_auth_flow():
  app = appmod.app
  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    r = await ac.get("/__ok"); assert r.status_code == 200 and r.json().get("ok") is True

    email, pw = "tester@example.com", "Test1234!"
    await ac.post("/auth/register", json={"email": email, "password": pw})

    r = await ac.post("/auth/login", json={"email": email, "password": pw}); assert r.status_code == 200
    at = r.json()["access_token"]

    r = await ac.get("/auth/me", headers={"Authorization": f"Bearer {at}"})
    assert r.status_code == 200 and r.json()["email"] == email

    doc = {"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"hello"}]}]}
    r = await ac.post("/content/", headers={"Authorization": f"Bearer {at}"}, json={"title":"T1","doc":doc}); assert r.status_code == 200
    cid = r.json()["id"]

    r = await ac.get("/content?limit=1", headers={"Authorization": f"Bearer {at}"}); assert r.status_code == 200

    r = await ac.put(f"/content/{cid}", headers={"Authorization": f"Bearer {at}"}, json={"title":"T1b","doc":doc}); assert r.status_code == 200
    r = await ac.delete(f"/content/{cid}", headers={"Authorization": f"Bearer {at}"}); assert r.status_code == 200 and r.json().get("ok") is True


