import os
import time
from typing import Tuple

from fastapi.testclient import TestClient
from jose import jwt
import pytest


def gen_rsa_keypair() -> Tuple[str, str]:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


ess_iss = "https://seedtest.local"
ess_aud = "seedtest-admin"


def make_token(private_pem: str, sub: str, roles, org_id: int | None = None):
    now = int(time.time())
    payload = {
        "iss": ess_iss,
        "aud": ess_aud,
        "sub": sub,
        "roles": roles,
        "iat": now,
        "exp": now + 3600,
    }
    if org_id is not None:
        payload["org_id"] = org_id
    tok = jwt.encode(payload, private_pem, algorithm="RS256")
    return tok


def setup_env_and_db(tmp_path):
    # Respect existing DATABASE_URL (e.g., CI Postgres). Otherwise use sqlite.
    if not os.environ.get("DATABASE_URL"):
        db_url = f"sqlite+pysqlite:///{tmp_path}/org.db?check_same_thread=False"
        os.environ["DATABASE_URL"] = db_url
    os.environ["LOCAL_DEV"] = "false"  # enforce JWT path
    from apps.seedtest_api.services import db as db_service
    from apps.seedtest_api.db.base import Base
    from apps.seedtest_api.models.question import QuestionRow

    engine = db_service.get_engine()
    # Safe to call even if Alembic already created the table (no-op)
    Base.metadata.create_all(engine, tables=[QuestionRow.__table__])


# Mark this module as DB-dependent to include it in CI's backend-db-tests job
pytestmark = pytest.mark.db


def test_org_enforcement_teacher_vs_teacher(tmp_path):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    t10 = make_token(priv, sub="t-10", roles=["teacher"], org_id=10)
    t20 = make_token(priv, sub="t-20", roles=["teacher"], org_id=20)

    # Teacher(10) creates a question (org_id=10)
    payload = {
        "stem": "문항 A",
        "options": ["A", "B"],
        "answer": 0,
        "difficulty": "easy",
        "topic": "대수",
        "tags": [],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload, headers={"Authorization": f"Bearer {t10}"})
    assert r.status_code in (200, 201), r.text
    q = r.json()
    qid = q["id"]

    # Teacher(20) cannot update Teacher(10)'s question → 403 forbidden_org
    payload_u = payload | {"difficulty": "medium"}
    r2 = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {t20}"})
    assert r2.status_code == 403

    # Teacher(20) cannot delete Teacher(10)'s question → 403
    r3 = client.delete(f"/api/seedtest/questions/{qid}", headers={"Authorization": f"Bearer {t20}"})
    assert r3.status_code == 403

    # Teacher(10) can update own question
    r4 = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {t10}"})
    assert r4.status_code == 200


def test_global_question_cannot_be_modified_by_teacher(tmp_path):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    admin = make_token(priv, sub="a-1", roles=["admin"])  # no org_id; acts global
    teacher = make_token(priv, sub="t-10", roles=["teacher"], org_id=10)

    # Admin creates a global question (org_id = NULL by default)
    payload = {
        "stem": "글로벌 문항",
        "options": ["A", "B", "C"],
        "answer": 1,
        "difficulty": "medium",
        "topic": "기하",
        "tags": [],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload, headers={"Authorization": f"Bearer {admin}"})
    assert r.status_code in (200, 201), r.text
    qid = r.json()["id"]

    # Teacher can GET (view) global question
    r2 = client.get(f"/api/seedtest/questions/{qid}", headers={"Authorization": f"Bearer {teacher}"})
    assert r2.status_code == 200

    # Teacher cannot UPDATE global question → 403 forbidden_global
    payload_u = payload | {"difficulty": "hard"}
    r3 = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {teacher}"})
    assert r3.status_code == 403

    # Teacher cannot DELETE global question → 403
    r4 = client.delete(f"/api/seedtest/questions/{qid}", headers={"Authorization": f"Bearer {teacher}"})
    assert r4.status_code == 403


def test_admin_global_edit_flag_false_blocks(tmp_path):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud
    # Ensure default flag false
    os.environ.pop("PLATFORM_GLOBAL_EDITABLE", None)

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    admin = make_token(priv, sub="a-1", roles=["admin"])  # no org_id; global

    payload = {"stem": "글로벌-Flag", "options": ["A", "B"], "answer": 0, "difficulty": "easy", "topic": "대수", "tags": [], "status": "draft"}
    r = client.post("/api/seedtest/questions", json=payload, headers={"Authorization": f"Bearer {admin}"})
    assert r.status_code in (200, 201)
    qid = r.json()["id"]
    payload_u = payload | {"difficulty": "medium"}
    r2 = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {admin}"})
    assert r2.status_code == 403


def test_admin_global_edit_flag_true_allows(tmp_path, monkeypatch):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    monkeypatch.setenv("JWT_PUBLIC_KEY", pub)
    monkeypatch.setenv("JWT_ISS", ess_iss)
    monkeypatch.setenv("JWT_AUD", ess_aud)
    # Enable flag before app import
    monkeypatch.setenv("PLATFORM_GLOBAL_EDITABLE", "true")

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    admin = make_token(priv, sub="a-1", roles=["admin"])  # no org_id; global
    payload = {"stem": "글로벌-Flag2", "options": ["A", "B"], "answer": 0, "difficulty": "easy", "topic": "대수", "tags": [], "status": "draft"}
    r = client.post("/api/seedtest/questions", json=payload, headers={"Authorization": f"Bearer {admin}"})
    assert r.status_code == 200
    qid = r.json()["id"]
    payload_u = payload | {"difficulty": "medium"}
    r2 = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {admin}"})
    assert r2.status_code == 200


def test_admin_can_create_org_scoped_and_teacher_cannot_override(tmp_path):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    admin = make_token(priv, sub="a-1", roles=["admin"])  # admin
    t10 = make_token(priv, sub="t-10", roles=["teacher"], org_id=10)

    # Admin creates an org-scoped question for org 30
    payload_admin = {
        "org_id": 30,
        "stem": "ORG30",
        "options": ["A", "B"],
        "answer": 0,
        "difficulty": "easy",
        "topic": "대수",
        "tags": [],
        "status": "draft",
    }
    r = client.post("/api/seedtest/questions", json=payload_admin, headers={"Authorization": f"Bearer {admin}"})
    assert r.status_code in (200, 201), r.text
    assert r.json().get("org_id") == 30

    # Teacher(10) attempting to create with org_id=20 should be forbidden
    payload_teacher = payload_admin | {"org_id": 20, "stem": "Bad"}
    r2 = client.post("/api/seedtest/questions", json=payload_teacher, headers={"Authorization": f"Bearer {t10}"})
    assert r2.status_code == 403

    # Teacher(10) creating without org_id should succeed and inherit org 10
    payload_teacher2 = {
        "stem": "MyOrg",
        "options": ["A", "B"],
        "answer": 0,
        "difficulty": "easy",
        "topic": "대수",
        "tags": [],
        "status": "draft",
    }
    r3 = client.post("/api/seedtest/questions", json=payload_teacher2, headers={"Authorization": f"Bearer {t10}"})
    assert r3.status_code == 200
    assert r3.json().get("org_id") == 10


def test_list_filters_teacher_sees_own_and_global(tmp_path):
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    admin = make_token(priv, sub="a-1", roles=["admin"])  # create global
    t10 = make_token(priv, sub="t-10", roles=["teacher"], org_id=10)
    t20 = make_token(priv, sub="t-20", roles=["teacher"], org_id=20)

    # Create global and per-org questions
    def create_with(tok, stem):
        p = {
            "stem": stem,
            "options": ["A", "B"],
            "answer": 0,
            "difficulty": "easy",
            "topic": "대수",
            "tags": [],
            "status": "draft",
        }
        return client.post("/api/seedtest/questions", json=p, headers={"Authorization": f"Bearer {tok}"})

    # global
    assert create_with(admin, "G1").status_code in (200, 201)
    assert create_with(admin, "G2").status_code in (200, 201)
    # org 10
    assert create_with(t10, "O10-1").status_code in (200, 201)
    # org 20
    assert create_with(t20, "O20-1").status_code in (200, 201)

    # Teacher(10) should see global + org10, but not org20
    r = client.get("/api/seedtest/questions?limit=50", headers={"Authorization": f"Bearer {t10}"})
    assert r.status_code == 200
    stems = [x["stem"] for x in r.json().get("results", [])]
    assert any(s.startswith("G") for s in stems)
    assert any(s.startswith("O10-") for s in stems)
    assert not any(s.startswith("O20-") for s in stems)

    # Admin can filter by org_id
    r2 = client.get("/api/seedtest/questions?org_id=20&limit=50", headers={"Authorization": f"Bearer {admin}"})
    assert r2.status_code == 200
    stems2 = [x["stem"] for x in r2.json().get("results", [])]
    assert any(s.startswith("O20-") for s in stems2)


def test_teacher_can_edit_own_global_when_created_by_self(tmp_path):
    """Teacher may edit a global question only if they are the original creator/author.

    We simulate a global question authored by the teacher by inserting it directly into the DB,
    since the create endpoint assigns org_id to the teacher's org by policy.
    """
    setup_env_and_db(tmp_path)
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = ess_iss
    os.environ["JWT_AUD"] = ess_aud

    from apps.seedtest_api.services import db as db_service
    from apps.seedtest_api.models.question import QuestionRow
    from apps.seedtest_api.db.base import Base

    # App import after env
    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    t10 = make_token(priv, sub="t-10", roles=["teacher"], org_id=10)

    # Insert a global question with created_by=teacher
    with db_service.get_session() as s:
        qid = "g-owned-by-t10"
        row = QuestionRow(
            id=qid,
            org_id=None,
            title=None,
            stem="Global by T10",
            explanation=None,
            options=["A", "B"],
            answer=0,
            difficulty="easy",
            topic="대수",
            topic_id=None,
            tags=["tag"],
            status="draft",
            author="t-10",
            created_by="t-10",
            updated_by="t-10",
        )
        s.add(row)
        s.flush()

    # Teacher can update their own global question
    payload_u = {
        "stem": "Global by T10 (edited)",
        "options": ["A", "B"],
        "answer": 1,
        "difficulty": "medium",
        "topic": "대수",
        "tags": ["tag"],
        "status": "draft",
    }
    r = client.put(f"/api/seedtest/questions/{qid}", json=payload_u, headers={"Authorization": f"Bearer {t10}"})
    assert r.status_code == 200, r.text
    assert r.json().get("stem") == "Global by T10 (edited)"

    # (no additional assertions here)
