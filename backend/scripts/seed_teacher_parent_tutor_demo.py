from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.core.database import SessionLocal
from app.models.user import User
from app.models.student import Student, Class, StudentClass
from app.models.tutor import TutorSession, TutorSessionTask
from app.models.ability_history import StudentAbilityHistory


def seed():
    db: Session = SessionLocal()

    try:
        # Create Users first
        teacher_user = User(
            email="teacher@example.com",
            hashed_password="hashed_teacher_pw",
            role="teacher",
            is_active=True,
        )
        db.add(teacher_user)
        
        tutor_user = User(
            email="tutor@example.com",
            hashed_password="hashed_tutor_pw",
            role="tutor",
            is_active=True,
        )
        db.add(tutor_user)
        
        student_user = User(
            email="student@example.com",
            hashed_password="hashed_student_pw",
            role="student",
            is_active=True,
        )
        db.add(student_user)
        
        db.commit()
        db.refresh(teacher_user)
        db.refresh(tutor_user)
        db.refresh(student_user)
        
        print(f"Created users: teacher_id={teacher_user.id}, tutor_id={tutor_user.id}, student_user_id={student_user.id}")
        
        teacher_id = teacher_user.id
        tutor_id = tutor_user.id
        student_user_id = student_user.id

        student = Student(
            user_id=student_user_id,
            name="홍길동",
            grade="G10",
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        clazz = Class(
            teacher_id=teacher_id,
            name="수학 1반",
            subject="Math",
            grade="G10",
        )
        db.add(clazz)
        db.commit()
        db.refresh(clazz)

        db.add(StudentClass(student_id=student.id, class_id=clazz.id))

        today = date.today()
        for i, theta in enumerate([-0.2, -0.1, 0.0, 0.1, 0.2]):
            db.add(
                StudentAbilityHistory(
                    student_id=student.id,
                    as_of_date=today - timedelta(days=(4 - i) * 7),
                    theta=theta,
                    source="seed",
                )
            )

        sess = TutorSession(
            tutor_id=tutor_id,
            student_id=student.id,
            date=today,
            subject="Math",
            topic="Derivatives",
            status="Completed",
            duration_minutes=90,
            notes="연습 필요",
        )
        db.add(sess)
        db.commit()
        db.refresh(sess)

        db.add(TutorSessionTask(session_id=sess.id, label="예제 5개 풀기", done=True))
        db.add(TutorSessionTask(session_id=sess.id, label="심화 문제 3개", done=False))

        db.commit()
        print("Seed completed successfully")
    except Exception as e:
        db.rollback()
        print("Seed failed:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
