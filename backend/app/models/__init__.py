"""
Database models for DreamSeed platform
"""

from .user import User
from .student import Student, Class, StudentClass
from .tutor import (
    Tutor,
    TutorSession,
    TutorSessionTask,
    TutorNote,
    TutorStudentRelation,
    TutorAvailability,
    TutorRating,
)
from .ability_history import StudentAbilityHistory
from .core_entities import (
    # Organization,  # Use org_models.Organization instead
    Teacher,
    StudentClassroom,
    # ExamSession,  # Use exam_models.ExamSession instead
    Attempt,  # Re-enabled for item_bank.py
)
from .org_models import Organization  # Primary Organization model
from .exam_models import ExamSession  # Primary ExamSession model
from .item import (
    Item,  # Primary Item model
    ItemChoice,
    ItemPool,
    ItemPoolMembership,
)
from .policy import (
    AuditLog,
    Approval,
    ParentApproval,
    StudentPolicy,
    TutorLog,
    StudentConsent,
    DeletionRequest,
)
from .zone import Zone
from .ai_request import AIRequest
from .messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
    ReadReceipt,
    NotificationSetting,
    InAppNotification,
    NotificationPreference,
    MessageReaction,
    Call,
    CallParticipant,
)
from .assignment_models import (
    Assignment,
    AssignmentStudent,
    Submission,
    SubmissionHistory,
)

__all__ = [
    "User",
    "Student",
    "Class",
    "StudentClass",
    # Tutor domain
    "Tutor",
    "TutorSession",
    "TutorSessionTask",
    "TutorNote",
    "TutorStudentRelation",
    "TutorAvailability",
    "TutorRating",
    "StudentAbilityHistory",
    # Core entities
    "Organization",
    "Teacher",
    "StudentClassroom",
    "ExamSession",
    "Attempt",  # Re-enabled
    # Items (IRT/CAT)
    "Item",
    "ItemChoice",
    "ItemPool",
    "ItemPoolMembership",
    # Policy/Approval/Audit
    "AuditLog",
    "Approval",
    "ParentApproval",
    "StudentPolicy",
    "TutorLog",
    "StudentConsent",
    "DeletionRequest",
    # Content organization
    "Zone",
    # AI tracking
    "AIRequest",
    # Messenger system
    "Conversation",
    "ConversationParticipant",
    "Message",
    "ReadReceipt",
    "NotificationSetting",
    "InAppNotification",
    "NotificationPreference",
    "MessageReaction",
    "Call",
    "CallParticipant",
    # Assignment system
    "Assignment",
    "AssignmentStudent",
    "Submission",
    "SubmissionHistory",
]
