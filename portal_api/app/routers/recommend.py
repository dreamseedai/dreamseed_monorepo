from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/")
def recommend(db: Session = Depends(get_db)):
    recs = []
    recs.append({"id": 1, "title": "Starter Assessment (5Q)", "reason": "first_login"})
    recs.append({"id": 2, "title": "Algebra Pre-Check", "reason": "grade_hint"})
    return {"items": recs}
