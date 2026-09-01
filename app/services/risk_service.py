from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase, RecoveryStatus


class RiskService:
    # High-priority transient failures with high recovery probability
    HIGH_RECOVERY_CODES = {
        "BAD_REQUEST_PAYMENT_TIMED_OUT",
        "GATEWAY_ERROR",
        "NETWORK_FAILURE",
        "BANK_SERVER_DOWN",
        "OTP_TIMEOUT"
    }

    # Liquidity or card limit failures requiring delayed reminders
    MEDIUM_RECOVERY_CODES = {
        "INSUFFICIENT_FUNDS",
        "PAYMENT_DECLINED",
        "LIMIT_EXCEEDED",
        "TRANSACTION_NOT_ALLOWED"
    }

    @classmethod
    def calculate_risk(cls, failure_reason: str | None, amount: float) -> tuple[float, str]:
        """
        Computes the risk score (0.0 to 1.0) and failure category.
        Score reflects probability & urgency of revenue recovery.
        """
        reason_upper = (failure_reason or "").upper()

        if any(code in reason_upper for code in cls.HIGH_RECOVERY_CODES):
            base_score = 0.90
            category = "TRANSIENT_TECHNICAL_FAILURE"
        elif any(code in reason_upper for code in cls.MEDIUM_RECOVERY_CODES):
            base_score = 0.65
            category = "CUSTOMER_LIQUIDITY_OR_LIMIT"
        elif "EXPIRED" in reason_upper or "INVALID" in reason_upper:
            base_score = 0.30
            category = "CARD_OR_ACCOUNT_INVALID"
        else:
            base_score = 0.50
            category = "UNCLASSIFIED_PAYMENT_FAILURE"

        # Higher amount at risk slightly increases recovery priority score
        amount_boost = min(amount / 50000.0, 0.10)
        final_score = round(min(base_score + amount_boost, 0.99), 2)

        return final_score, category

    @classmethod
    def detect_and_create_recovery_case(
        cls,
        db: Session,
        merchant_id: str,
        payment_event: PaymentEvent
    ) -> tuple[RecoveryCase, bool]:
        """
        Analyzes a payment failure event and initializes a RecoveryCase if not already present.
        Returns tuple of (RecoveryCase, is_new).
        """
        stmt = select(RecoveryCase).where(RecoveryCase.payment_event_id == payment_event.id)
        existing_case = db.execute(stmt).scalar_one_or_none()

        if existing_case:
            return existing_case, False

        risk_score, _ = cls.calculate_risk(payment_event.failure_reason, payment_event.amount)

        recovery_case = RecoveryCase(
            merchant_id=merchant_id,
            payment_event_id=payment_event.id,
            status=RecoveryStatus.DETECTED.value,
            risk_score=risk_score,
            amount_at_risk=payment_event.amount,
            customer_name=None,
            customer_email=payment_event.customer_email,
            recovery_attempts=0,
            max_allowed_attempts=3
        )

        db.add(recovery_case)
        db.commit()
        db.refresh(recovery_case)

        return recovery_case, True
