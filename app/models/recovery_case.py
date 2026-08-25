import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecoveryStatus(str, Enum):
    DETECTED = "DETECTED"
    ANALYZING = "ANALYZING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), index=True, nullable=False)
    payment_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("payment_events.id"), unique=True, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default=RecoveryStatus.DETECTED.value, index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    amount_at_risk: Mapped[float] = mapped_column(Float, nullable=False)

    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    recovery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_allowed_attempts: Mapped[int] = mapped_column(Integer, default=3)

    last_action_taken: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="recovery_cases")
    payment_event: Mapped["PaymentEvent"] = relationship("PaymentEvent", back_populates="recovery_case")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="recovery_case", cascade="all, delete-orphan")
