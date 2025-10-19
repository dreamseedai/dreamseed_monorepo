from contextlib import contextmanager
from sqlalchemy import text
from .db import SessionLocal

@contextmanager
def rls_session(org_id: int | None, is_admin: bool = False):
    db = SessionLocal()
    try:
        with db.begin():
            if org_id is not None:
                db.execute(text("SET LOCAL seedtest.org_id = :oid"), {"oid": org_id})
            # Optional: admin bypass via local flag (if extended server-side)
            # db.execute(text("SET LOCAL seedtest.is_admin = :adm"), {"adm": 'true' if is_admin else 'false'})
            yield db
    finally:
        db.close()
