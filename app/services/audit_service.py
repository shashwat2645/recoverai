from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.audit_log import AuditLog


class AuditService:
    @classmethod
    def create_audit_log(
        cls,
        db: Session,
        recovery_case_id: str,
        merchant_id: str,
        event_type: str,
        prompt_context: dict | None = None,
        ai_reasoning: str | None = None,
        confidence_score: float | None = None,
        recommended_action: str = "GENERATE_PAYMENT_LINK",
        executed_action: str | None = None,
        execution_status: str = "PENDING"
    ) -> AuditLog:
        """
        Persists an immutable audit log capturing input state, prompt context, AI reasoning,
        confidence scores, and action execution status.
        """
        audit_entry = AuditLog(
            recovery_case_id=recovery_case_id,
            merchant_id=merchant_id,
            event_type=event_type,
            prompt_context=prompt_context,
            ai_reasoning=ai_reasoning,
            confidence_score=confidence_score,
            recommended_action=recommended_action,
            executed_action=executed_action,
            execution_status=execution_status
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @classmethod
    def get_audit_logs_for_case(cls, db: Session, case_id: str, merchant_id: str) -> list[AuditLog]:
        """
        Retrieves all chronological audit logs for a specific recovery case.
        """
        stmt = select(AuditLog).where(
            AuditLog.recovery_case_id == case_id,
            AuditLog.merchant_id == merchant_id
        ).order_by(AuditLog.created_at.asc())
        return db.execute(stmt).scalars().all()

    @classmethod
    def get_merchant_audit_logs(cls, db: Session, merchant_id: str, limit: int = 50) -> list[AuditLog]:
        """
        Retrieves latest global audit logs for a merchant.
        """
        stmt = select(AuditLog).where(
            AuditLog.merchant_id == merchant_id
        ).order_by(AuditLog.created_at.desc()).limit(limit)
        return db.execute(stmt).scalars().all()
