# backend/app/auth/dependencies.py


def get_optional_user():
    # TODO: 실제 인증 로직으로 교체
    return {"id": 1, "email": "dev@myktube.com", "role": "admin"}
