from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import sql_query_execution_repo
from app.services.sql.operation_classifier import OperationRiskLevel, OperationType


class ApprovalStatus(str, Enum):
    """Approval workflow status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    EXECUTED = "executed"


class OperationApprovalRequest:
    """Encapsulates an operation awaiting approval."""
    
    def __init__(
        self,
        execution_id: uuid.UUID,
        operation_type: OperationType,
        risk_level: OperationRiskLevel,
        risk_messages: list[str],
        generated_sql: str,
        sql_explanation: str | None,
        question: str,
    ):
        self.execution_id = execution_id
        self.operation_type = operation_type
        self.risk_level = risk_level
        self.risk_messages = risk_messages
        self.generated_sql = generated_sql
        self.sql_explanation = sql_explanation
        self.question = question
        self.approval_status = ApprovalStatus.PENDING
        self.approval_reason: str | None = None
        self.approved_at: datetime | None = None
        self.approved_by_user_id: uuid.UUID | None = None
    
    def approve(self, user_id: uuid.UUID, reason: str = "") -> None:
        """Mark operation as approved."""
        self.approval_status = ApprovalStatus.APPROVED
        self.approval_reason = reason
        self.approved_at = datetime.now(timezone.utc)
        self.approved_by_user_id = user_id
    
    def reject(self, user_id: uuid.UUID, reason: str = "") -> None:
        """Mark operation as rejected."""
        self.approval_status = ApprovalStatus.REJECTED
        self.approval_reason = reason
        self.approved_at = datetime.now(timezone.utc)
        self.approved_by_user_id = user_id
    
    def auto_approve(self) -> None:
        """Mark operation as auto-approved (low risk, doesn't need confirmation)."""
        self.approval_status = ApprovalStatus.AUTO_APPROVED
        self.approved_at = datetime.now(timezone.utc)
    
    def is_approved(self) -> bool:
        """Check if operation is approved or auto-approved."""
        return self.approval_status in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED)
    
    def is_rejected(self) -> bool:
        """Check if operation was rejected."""
        return self.approval_status == ApprovalStatus.REJECTED
    
    def is_pending(self) -> bool:
        """Check if operation is pending approval."""
        return self.approval_status == ApprovalStatus.PENDING


def determine_requires_approval(operation_type: OperationType, risk_level: OperationRiskLevel) -> bool:
    """
    Determine if an operation requires user approval.
    
    Critical and high-risk operations always require approval.
    """
    if risk_level in (OperationRiskLevel.CRITICAL, OperationRiskLevel.HIGH):
        return True
    if operation_type in (
        OperationType.SCHEMA_DROP,
        OperationType.SCHEMA_ALTER,
        OperationType.ADMIN,
    ):
        return True
    return False


def create_approval_request(
    operation_type: OperationType,
    risk_level: OperationRiskLevel,
    risk_messages: list[str],
    generated_sql: str,
    sql_explanation: str | None,
    question: str,
) -> OperationApprovalRequest:
    """Create a new approval request."""
    execution_id = uuid.uuid4()
    request = OperationApprovalRequest(
        execution_id=execution_id,
        operation_type=operation_type,
        risk_level=risk_level,
        risk_messages=risk_messages,
        generated_sql=generated_sql,
        sql_explanation=sql_explanation,
        question=question,
    )
    
    # Auto-approve low-risk operations that don't require approval
    if not determine_requires_approval(operation_type, risk_level):
        request.auto_approve()
    
    return request
