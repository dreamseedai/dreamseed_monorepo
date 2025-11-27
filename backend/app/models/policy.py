"""
Policy, Approval & Audit Models

정책/승인/감사 레이어 엔티티:
- AuditLog: 감사 추적
- Approval: 공통 승인 요청
- ParentApproval: 학부모-자녀 승인
- StudentPolicy: AI 사용 정책
- TutorLog: AI 튜터 로그
- StudentConsent: 동의 관리
- DeletionRequest: 데이터 삭제 요청
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, Boolean, 
    ForeignKey, Text, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """
    감사 로그 - 모든 중요한 시스템 이벤트 추적
    
    사용 예:
    - 승인 처리 기록
    - 데이터 접근 추적
    - 정책 위반 기록
    - 관리자 작업 감사
    """
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    event_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(BigInteger)
    action = Column(String(50))
    description = Column(Text)
    details_json = Column(JSONB)
    ip_address = Column(String(64))
    user_agent = Column(Text)

    # Relationships
    user = relationship("User", backref="audit_logs")
    organization = relationship("Organization", backref="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, action={self.action})>"


class Approval(Base):
    """
    공통 승인 요청 - 재시험, 특별 접근, AI 콘텐츠 승인 등
    
    사용 예:
    - 재시험 요청 (request_type='retest')
    - 상위 시험 접근 (request_type='special_access')
    - AI 생성 콘텐츠 승인 (request_type='content')
    - 플랜 업그레이드 (request_type='plan_upgrade')
    """
    __tablename__ = "approvals"

    id = Column(BigInteger, primary_key=True)
    request_type = Column(String(50), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approver_role = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(BigInteger)
    status = Column(String(20), default="pending", nullable=False, index=True)
    request_data = Column(JSONB)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    requester = relationship(
        "User", 
        foreign_keys=[requester_id], 
        backref="approval_requests"
    )
    approver = relationship(
        "User", 
        foreign_keys=[approved_by], 
        backref="approval_decisions"
    )

    __table_args__ = (
        Index("idx_approvals_resource", "resource_type", "resource_id"),
    )

    def __repr__(self):
        return f"<Approval(id={self.id}, type={self.request_type}, status={self.status})>"


class ParentApproval(Base):
    """
    학부모-자녀 관계 승인
    
    학부모가 자녀 계정에 접근하기 위한 승인 프로세스
    """
    __tablename__ = "parent_approvals"

    id = Column(BigInteger, primary_key=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Relationships
    parent = relationship(
        "User", 
        foreign_keys=[parent_user_id], 
        backref="parent_approvals"
    )
    student = relationship("Student", backref="parent_approvals")
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("uq_parent_student", "parent_user_id", "student_id", unique=True),
    )

    def __repr__(self):
        return f"<ParentApproval(id={self.id}, parent={self.parent_user_id}, student={self.student_id}, status={self.status})>"


class StudentPolicy(Base):
    """
    학생별 AI 사용 정책
    
    학생별로 AI 튜터 사용을 제어:
    - AI 튜터 활성화 여부
    - 일일 질문 제한
    - 시험 중 사용 금지
    """
    __tablename__ = "student_policies"

    id = Column(BigInteger, primary_key=True)
    student_id = Column(
        Integer, 
        ForeignKey("students.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False,
        index=True
    )
    ai_tutor_enabled = Column(Boolean, default=True, nullable=False)
    daily_question_limit = Column(Integer)  # NULL = unlimited
    restricted_during_exam = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    meta = Column(JSONB)

    # Relationships
    student = relationship("Student", backref="policy", uselist=False)
    updated_by_user = relationship("User")

    def __repr__(self):
        return f"<StudentPolicy(student_id={self.student_id}, ai_enabled={self.ai_tutor_enabled})>"


class TutorLog(Base):
    """
    AI 튜터 대화 로그
    
    품질 모니터링 및 감사를 위한 AI 튜터 대화 기록
    """
    __tablename__ = "tutor_logs"

    id = Column(BigInteger, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    session_id = Column(BigInteger, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    model_used = Column(String(50))
    context_json = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    student = relationship("Student", backref="tutor_logs")

    def __repr__(self):
        return f"<TutorLog(id={self.id}, student_id={self.student_id}, model={self.model_used})>"


class StudentConsent(Base):
    """
    학생 동의 관리
    
    GDPR/COPPA/개인정보보호법 준수를 위한 동의/철회 기록
    """
    __tablename__ = "student_consents"

    id = Column(BigInteger, primary_key=True)
    student_id = Column(
        Integer, 
        ForeignKey("students.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    parent_user_id = Column(Integer, ForeignKey("users.id"))
    consent_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # 'granted', 'revoked'
    granted_at = Column(DateTime)
    revoked_at = Column(DateTime)
    meta = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("Student", backref="consents")
    parent = relationship("User")

    __table_args__ = (
        Index("idx_student_consents_status", "consent_type", "status"),
    )

    def __repr__(self):
        return f"<StudentConsent(id={self.id}, student_id={self.student_id}, type={self.consent_type}, status={self.status})>"


class DeletionRequest(Base):
    """
    데이터 삭제 요청
    
    GDPR "잊힐 권리" 구현을 위한 데이터 삭제 요청 추적
    """
    __tablename__ = "deletion_requests"

    id = Column(BigInteger, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending", nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    processed_at = Column(DateTime)
    meta = Column(JSONB)

    # Relationships
    student = relationship("Student", backref="deletion_requests")
    requester = relationship(
        "User", 
        foreign_keys=[requested_by], 
        backref="data_deletion_requests"
    )
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<DeletionRequest(id={self.id}, student_id={self.student_id}, status={self.status})>"
