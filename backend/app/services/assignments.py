"""
Assignment Service - Business logic for homework management system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment_models import (
    Assignment,
    AssignmentStudent,
    Submission,
    SubmissionHistory,
)


class AssignmentType(str, Enum):
    """Assignment types"""

    HOMEWORK = "homework"
    QUIZ = "quiz"
    TEST = "test"
    PROJECT = "project"


class AssignmentStatus(str, Enum):
    """Assignment statuses"""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class SubmissionStatus(str, Enum):
    """Submission statuses"""

    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class AssignmentService:
    """Service class for assignment operations."""

    @staticmethod
    async def create_assignment(
        db: AsyncSession,
        title: str,
        teacher_id: int,
        assignment_type: AssignmentType,
        student_ids: List[int],
        description: Optional[str] = None,
        class_id: Optional[str] = None,
        subject: Optional[str] = None,
        grade: Optional[str] = None,
        template_id: Optional[str] = None,
        total_points: Optional[int] = None,
        due_date: Optional[datetime] = None,
        instructions: Optional[str] = None,
        attachments: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: AssignmentStatus = AssignmentStatus.ACTIVE,
    ) -> Assignment:
        """
        Create a new assignment and assign it to students.

        Args:
            db: Database session
            title: Assignment title
            teacher_id: Teacher creating the assignment
            assignment_type: Type of assignment (homework, quiz, etc.)
            student_ids: List of student IDs to assign to
            Other optional parameters

        Returns:
            Created assignment
        """
        # Create assignment
        assignment = Assignment(
            title=title,
            description=description,
            teacher_id=teacher_id,
            class_id=class_id,
            subject=subject,
            grade=grade,
            assignment_type=assignment_type.value,
            template_id=template_id,
            total_points=total_points,
            due_date=due_date,
            assigned_date=datetime.utcnow(),
            status=status.value,
            instructions=instructions,
            attachments=attachments,
            assignment_metadata=metadata,
        )
        db.add(assignment)
        await db.flush()

        # Assign to students
        for student_id in student_ids:
            assignment_student = AssignmentStudent(
                assignment_id=assignment.id,
                student_id=student_id,
            )
            db.add(assignment_student)

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def get_assignment(
        db: AsyncSession,
        assignment_id: int,
        teacher_id: Optional[int] = None,
    ) -> Optional[Assignment]:
        """
        Get assignment by ID.

        Args:
            db: Database session
            assignment_id: Assignment ID
            teacher_id: Optional teacher ID for permission check

        Returns:
            Assignment or None
        """
        stmt = select(Assignment).where(Assignment.id == assignment_id)

        if teacher_id:
            stmt = stmt.where(Assignment.teacher_id == teacher_id)

        stmt = stmt.options(
            selectinload(Assignment.assignment_students),
            selectinload(Assignment.submissions),
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_teacher_assignments(
        db: AsyncSession,
        teacher_id: int,
        class_id: Optional[str] = None,
        status: Optional[AssignmentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Assignment]:
        """
        Get assignments created by a teacher.

        Args:
            db: Database session
            teacher_id: Teacher ID
            class_id: Optional filter by class
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of assignments
        """
        stmt = select(Assignment).where(Assignment.teacher_id == teacher_id)

        if class_id:
            stmt = stmt.where(Assignment.class_id == class_id)

        if status:
            stmt = stmt.where(Assignment.status == status.value)

        stmt = (
            stmt.order_by(Assignment.assigned_date.desc()).limit(limit).offset(offset)
        )
        stmt = stmt.options(
            selectinload(Assignment.assignment_students),
            selectinload(Assignment.submissions),
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_student_assignments(
        db: AsyncSession,
        student_id: int,
        status: Optional[AssignmentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Assignment]:
        """
        Get assignments assigned to a student.

        Args:
            db: Database session
            student_id: Student ID
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of assignments
        """
        stmt = (
            select(Assignment)
            .join(AssignmentStudent)
            .where(AssignmentStudent.student_id == student_id)
        )

        if status:
            stmt = stmt.where(Assignment.status == status.value)

        stmt = stmt.order_by(Assignment.due_date.asc()).limit(limit).offset(offset)
        stmt = stmt.options(selectinload(Assignment.submissions))

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_assignment(
        db: AsyncSession, assignment_id: int, teacher_id: int, **kwargs
    ) -> Optional[Assignment]:
        """
        Update an assignment.

        Args:
            db: Database session
            assignment_id: Assignment ID
            teacher_id: Teacher ID (for permission check)
            **kwargs: Fields to update

        Returns:
            Updated assignment or None
        """
        assignment = await AssignmentService.get_assignment(
            db, assignment_id, teacher_id
        )

        if not assignment:
            return None

        for key, value in kwargs.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)

        assignment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def delete_assignment(
        db: AsyncSession,
        assignment_id: int,
        teacher_id: int,
    ) -> bool:
        """
        Delete an assignment.

        Args:
            db: Database session
            assignment_id: Assignment ID
            teacher_id: Teacher ID (for permission check)

        Returns:
            True if deleted, False otherwise
        """
        assignment = await AssignmentService.get_assignment(
            db, assignment_id, teacher_id
        )

        if not assignment:
            return False

        await db.delete(assignment)
        await db.commit()
        return True

    @staticmethod
    async def submit_assignment(
        db: AsyncSession,
        assignment_id: int,
        student_id: int,
        submission_text: Optional[str] = None,
        attachments: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Submission:
        """
        Submit an assignment (student creates submission).

        Args:
            db: Database session
            assignment_id: Assignment ID
            student_id: Student ID
            submission_text: Text content of submission
            attachments: File attachments
            metadata: Additional metadata

        Returns:
            Created submission
        """
        # Get assignment to check due date
        assignment = await AssignmentService.get_assignment(db, assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        # Check if already submitted
        stmt = select(Submission).where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.utcnow()
        is_late = assignment.due_date and now > assignment.due_date

        if existing:
            # Update existing submission (resubmission)
            # Save history
            history = SubmissionHistory(
                submission_id=existing.id,
                version=len(existing.history) + 1,
                submission_text=existing.submission_text,
                attachments=existing.attachments,
                submitted_at=existing.submitted_at,
            )
            db.add(history)

            # Update submission
            existing.submission_text = submission_text
            existing.attachments = attachments
            existing.submitted_at = now
            existing.is_late = is_late if is_late is not None else False
            existing.status = SubmissionStatus.SUBMITTED.value
            existing.submission_metadata = metadata
            existing.updated_at = now

            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new submission
            submission = Submission(
                assignment_id=assignment_id,
                student_id=student_id,
                submission_text=submission_text,
                attachments=attachments,
                submitted_at=now,
                is_late=is_late,
                status=SubmissionStatus.SUBMITTED.value,
                submission_metadata=metadata,
            )
            db.add(submission)
            await db.commit()
            await db.refresh(submission)
            return submission

    @staticmethod
    async def grade_submission(
        db: AsyncSession,
        submission_id: int,
        grader_id: int,
        score: Optional[int] = None,
        grade: Optional[str] = None,
        feedback: Optional[str] = None,
        rubric_scores: Optional[Dict[str, Any]] = None,
    ) -> Optional[Submission]:
        """
        Grade a submission (teacher grades student work).

        Args:
            db: Database session
            submission_id: Submission ID
            grader_id: Teacher ID grading the submission
            score: Numeric score
            grade: Letter grade
            feedback: Written feedback
            rubric_scores: Rubric breakdown

        Returns:
            Graded submission or None
        """
        stmt = select(Submission).where(Submission.id == submission_id)
        stmt = stmt.options(selectinload(Submission.assignment))
        result = await db.execute(stmt)
        submission = result.scalar_one_or_none()

        if not submission:
            return None

        # Update grading
        submission.score = score
        submission.grade = grade
        submission.feedback = feedback
        submission.rubric_scores = rubric_scores
        submission.graded_at = datetime.utcnow()
        submission.graded_by = grader_id
        submission.status = SubmissionStatus.GRADED.value
        submission.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def get_assignment_submissions(
        db: AsyncSession,
        assignment_id: int,
        teacher_id: int,
        status: Optional[SubmissionStatus] = None,
    ) -> List[Submission]:
        """
        Get all submissions for an assignment (teacher view).

        Args:
            db: Database session
            assignment_id: Assignment ID
            teacher_id: Teacher ID (for permission check)
            status: Optional filter by submission status

        Returns:
            List of submissions
        """
        # Verify teacher owns the assignment
        assignment = await AssignmentService.get_assignment(
            db, assignment_id, teacher_id
        )
        if not assignment:
            return []

        stmt = select(Submission).where(Submission.assignment_id == assignment_id)

        if status:
            stmt = stmt.where(Submission.status == status.value)

        stmt = stmt.order_by(Submission.submitted_at.desc())
        stmt = stmt.options(selectinload(Submission.history))

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_student_submission(
        db: AsyncSession,
        assignment_id: int,
        student_id: int,
    ) -> Optional[Submission]:
        """
        Get a student's submission for an assignment.

        Args:
            db: Database session
            assignment_id: Assignment ID
            student_id: Student ID

        Returns:
            Submission or None
        """
        stmt = select(Submission).where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
        )
        stmt = stmt.options(
            selectinload(Submission.assignment), selectinload(Submission.history)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_assignment_statistics(
        db: AsyncSession,
        assignment_id: int,
        teacher_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for an assignment.

        Args:
            db: Database session
            assignment_id: Assignment ID
            teacher_id: Teacher ID (for permission check)

        Returns:
            Statistics dictionary or None
        """
        # Verify teacher owns the assignment
        assignment = await AssignmentService.get_assignment(
            db, assignment_id, teacher_id
        )
        if not assignment:
            return None

        # Count students assigned
        stmt = select(func.count(AssignmentStudent.id)).where(
            AssignmentStudent.assignment_id == assignment_id
        )
        result = await db.execute(stmt)
        total_students = result.scalar()

        # Count submissions
        stmt = select(func.count(Submission.id)).where(
            Submission.assignment_id == assignment_id
        )
        result = await db.execute(stmt)
        submitted_count = result.scalar()

        # Count graded submissions
        stmt = select(func.count(Submission.id)).where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.status == SubmissionStatus.GRADED.value,
            )
        )
        result = await db.execute(stmt)
        graded_count = result.scalar()

        # Count late submissions
        stmt = select(func.count(Submission.id)).where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.is_late == True,
            )
        )
        result = await db.execute(stmt)
        late_count = result.scalar()

        # Average score
        stmt = select(func.avg(Submission.score)).where(
            and_(
                Submission.assignment_id == assignment_id,
                Submission.score.isnot(None),
            )
        )
        result = await db.execute(stmt)
        avg_score = result.scalar()

        # Handle None values with defaults
        total_students = total_students or 0
        submitted_count = submitted_count or 0
        graded_count = graded_count or 0
        late_count = late_count or 0

        return {
            "assignment_id": assignment_id,
            "total_students": total_students,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "late_count": late_count,
            "pending_count": submitted_count - graded_count,
            "not_submitted_count": total_students - submitted_count,
            "avg_score": float(avg_score) if avg_score else None,
            "submission_rate": (
                (submitted_count / total_students * 100) if total_students > 0 else 0
            ),
            "grading_rate": (
                (graded_count / submitted_count * 100) if submitted_count > 0 else 0
            ),
        }


def get_assignment_service() -> AssignmentService:
    """Dependency injection for assignment service."""
    return AssignmentService()
