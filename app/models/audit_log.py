import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recovery_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_cases.id"), index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # RAG Context & LLM Diagnostics
    prompt_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    executed_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_status: Mapped[str] = mapped_column(String(50), default="PENDING")  # SUCCESS, BLOCKED_BY_GUARDRAIL, FAILED

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    recovery_case: Mapped["RecoveryCase"] = relationship("RecoveryCase", back_populates="audit_logs")
