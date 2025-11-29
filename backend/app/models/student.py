"""
Student and Class models
"""
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    """Student model - represents learners in the platform"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    external_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    grade = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    classes = relationship("StudentClass", back_populates="student")

    def __repr__(self):
        return f"<Student(id={self.id}, name={self.name}, grade={self.grade})>"


class Class(Base):
    """Class model - represents a teacher's class/section"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(Text, nullable=False)
    subject = Column(Text, nullable=True)
    grade = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    students = relationship("StudentClass", back_populates="clazz")

    def __repr__(self):
        return f"<Class(id={self.id}, name={self.name}, subject={self.subject})>"


class StudentClass(Base):
    """Many-to-many relationship between students and classes"""
    __tablename__ = "student_classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="classes")
    clazz = relationship("Class", back_populates="students")

    __table_args__ = (
        UniqueConstraint("student_id", "class_id", name="uq_student_class"),
    )

    def __repr__(self):
        return f"<StudentClass(student_id={self.student_id}, class_id={self.class_id})>"
