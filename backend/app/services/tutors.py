# backend/app/services/tutors.py
"""
Service layer for tutor-related operations
"""
from typing import List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.tutor import TutorSession, TutorSessionTask
from app.schemas.tutors import (
    TutorSessionSummary,
    TutorSessionDetail,
    SessionStatus,
    TutorSessionTask as TutorSessionTaskSchema,
)


def list_sessions_for_tutor(
    db: Session,
    tutor_id: int,
    status: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[List[TutorSessionSummary], int]:
    stmt = select(TutorSession).where(TutorSession.id.isnot(None))  # base query

    stmt = stmt.where(TutorSession.tutor_id == tutor_id)

    if status and status != "all":
        stmt = stmt.where(TutorSession.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    sessions = db.scalars(stmt).all()
    results: List[TutorSessionSummary] = []
    for sess in sessions:
        results.append(
            TutorSessionSummary(
                id=str(sess.id),
                date=str(sess.date),
                student_id=str(sess.student_id),
                student_name="",  # fill when you join with Student
                subject=str(sess.subject or ""),
                topic=str(sess.topic or ""),
                status=cast(SessionStatus, sess.status),
            )
        )

    return results, total or 0


def get_session_detail(
    db: Session,
    tutor_id: int,
    session_id: int,
) -> Optional[TutorSessionDetail]:
    sess = db.get(TutorSession, session_id)
    if sess is None:
        return None

    sess = cast(TutorSession, sess)
    if cast(int, sess.tutor_id) != tutor_id:
        return None

    tasks = db.query(TutorSessionTask).filter(TutorSessionTask.session_id == session_id).all()

    duration_minutes = cast(Optional[int], sess.duration_minutes)

    return TutorSessionDetail(
        id=str(sess.id),
        date=str(sess.date),
        student_id=str(sess.student_id),
        student_name="",
        subject=str(sess.subject or ""),
        topic=str(sess.topic or ""),
        status=cast(SessionStatus, sess.status),
        duration_minutes=duration_minutes,
        notes=cast(Optional[str], sess.notes) or "",
        tasks=[
            TutorSessionTaskSchema(
                label=str(t.label),
                done=bool(t.done),
            )
            for t in tasks
        ],
    )
