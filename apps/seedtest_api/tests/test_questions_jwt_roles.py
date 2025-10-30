import os
import time
from typing import Tuple

from fastapi.testclient import TestClient
from jose import jwt


def gen_rsa_keypair() -> Tuple[str, str]:
    # Generate RSA keypair using cryptography
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


def make_token(private_pem: str, sub: str, roles):
    iss = "https://seedtest.local"
    aud = "seedtest-admin"
    now = int(time.time())
    payload = {
        "iss": iss,
        "aud": aud,
        "sub": sub,
        "roles": roles,
        "iat": now,
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, private_pem, algorithm="RS256")
    return tok, iss, aud


def test_questions_role_guard_with_jwt(tmp_path):
    # Setup DB
    db_url = f"sqlite+pysqlite:///{tmp_path}/jwt.db?check_same_thread=False"
    os.environ["DATABASE_URL"] = db_url
    # Ensure LOCAL_DEV is off to exercise JWT path
    os.environ["LOCAL_DEV"] = "false"

    # Create empty DB
    from apps.seedtest_api.services import db as db_service
    from apps.seedtest_api.db.base import Base
    from apps.seedtest_api.models.question import QuestionRow

    engine = db_service.get_engine()
    Base.metadata.create_all(engine, tables=[QuestionRow.__table__])

    # Generate keys and configure settings env
    priv, pub = gen_rsa_keypair()
    os.environ["JWT_PUBLIC_KEY"] = pub
    os.environ["JWT_ISS"] = "https://seedtest.local"
    os.environ["JWT_AUD"] = "seedtest-admin"

    from apps.seedtest_api.app.main import app
    client = TestClient(app)

    teacher_token, iss, aud = make_token(priv, sub="t-1", roles=["teacher"])  # teacher
    student_token, _, _ = make_token(priv, sub="s-1", roles=["student"])  # student

    # Teacher can list (even if empty)
    r = client.get("/api/seedtest/questions", headers={"Authorization": f"Bearer {teacher_token}"})
    assert r.status_code == 200

    # Student forbidden for questions endpoints (list)
    r2 = client.get("/api/seedtest/questions", headers={"Authorization": f"Bearer {student_token}"})
    assert r2.status_code == 403

    # Teacher can create
    payload = {
        "stem": "JWT 문항",
        "options": ["A", "B"],
        "answer": 0,
        "difficulty": "medium",
        "topic": "대수",
        "tags": [],
        "status": "draft",
    }
    r3 = client.post("/api/seedtest/questions", json=payload, headers={"Authorization": f"Bearer {teacher_token}"})
    assert r3.status_code in (200, 201)

    # Student still forbidden to list after create
    r4 = client.get("/api/seedtest/questions", headers={"Authorization": f"Bearer {student_token}"})
    assert r4.status_code == 403
