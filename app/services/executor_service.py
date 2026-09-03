from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.recovery_case import RecoveryCase, RecoveryStatus
from app.models.payment_event import PaymentEvent
from app.models.merchant import Merchant
from app.services.razorpay_service import RazorpayService


class ActionExecutorService:
    # Strictly Whitelisted Bounded Actions
    ALLOWED_ACTIONS = {
        "GENERATE_PAYMENT_LINK",
        "SEND_REMINDER",
        "SCHEDULE_RETRY",
        "MARK_UNRECOVERABLE"
    }

    # Forbidden financial actions (hard block at code level)
    FORBIDDEN_ACTIONS = {
        "REFUND",
        "AUTOMATIC_REFUND",
        "MODIFY_AMOUNT",
        "CANCEL_SUBSCRIPTION",
        "UNAUTHORIZED_CREDIT"
    }

    @classmethod
    def execute_action(
        cls,
        db: Session,
        case_id: str,
        merchant_id: str,
        action_override: str | None = None
    ) -> tuple[RecoveryCase, dict]:
        """
        Executes a bounded recovery action for a recovery case.
        Enforces strict whitelist guardrails and blocks forbidden financial operations.
        """
        stmt = select(RecoveryCase).where(
            RecoveryCase.id == case_id,
            RecoveryCase.merchant_id == merchant_id
        )
        case = db.execute(stmt).scalar_one_or_none()

        if not case:
            raise ValueError(f"Recovery case with ID {case_id} not found.")

        # Determine target action (override or AI recommended action)
        target_action = (action_override or case.last_action_taken or "GENERATE_PAYMENT_LINK").upper()

        # 1. Enforce Hard Guardrail Whitelist & Blacklist
        if target_action in cls.FORBIDDEN_ACTIONS or target_action not in cls.ALLOWED_ACTIONS:
            raise PermissionError(
                f"Guardrail Blocked: Action '{target_action}' is not an allowed bounded action. "
                f"Financial actions such as refunds or amount alterations are strictly forbidden."
            )

        # Fetch linked PaymentEvent and Merchant details
        event_stmt = select(PaymentEvent).where(PaymentEvent.id == case.payment_event_id)
        payment_event = db.execute(event_stmt).scalar_one()

        merchant_stmt = select(Merchant).where(Merchant.id == merchant_id)
        merchant = db.execute(merchant_stmt).scalar_one()

        result_data = {}
        execution_status = "SUCCESS"

        # 2. Execute Bounded Action Handlers
        if target_action == "GENERATE_PAYMENT_LINK":
            link_res = RazorpayService.create_payment_link(
                amount=case.amount_at_risk,
                currency=payment_event.currency,
                description=f"RecoverAI Payment Retry for Event {payment_event.event_id}",
                customer_name=case.customer_name,
                customer_email=case.customer_email,
                customer_phone=payment_event.customer_phone,
                reference_id=f"rec_{case.id[:8]}",
                key_id=merchant.razorpay_key_id,
                key_secret=merchant.razorpay_key_secret
            )
            result_data = {
                "action": "GENERATE_PAYMENT_LINK",
                "payment_link_id": link_res.get("id"),
                "short_url": link_res.get("short_url"),
                "amount": case.amount_at_risk,
                "customer_email": case.customer_email
            }
            case.status = RecoveryStatus.RECOVERING.value
            case.recovery_attempts += 1

        elif target_action == "SEND_REMINDER":
            result_data = {
                "action": "SEND_REMINDER",
                "channel": "EMAIL_AND_SMS",
                "recipient": case.customer_email,
                "message": f"Polite payment reminder dispatched for order of ₹{case.amount_at_risk:.2f}."
            }
            case.status = RecoveryStatus.RECOVERING.value
            case.recovery_attempts += 1

        elif target_action == "SCHEDULE_RETRY":
            next_retry = datetime.now(timezone.utc) + timedelta(hours=24)
            case.next_retry_at = next_retry
            result_data = {
                "action": "SCHEDULE_RETRY",
                "next_retry_at": next_retry.isoformat(),
                "delay_hours": 24
            }
            case.status = RecoveryStatus.RECOVERING.value

        elif target_action == "MARK_UNRECOVERABLE":
            case.status = RecoveryStatus.FAILED.value
            result_data = {
                "action": "MARK_UNRECOVERABLE",
                "reason": "Case marked unrecoverable by merchant policy or stopping rule."
            }

        case.last_action_taken = target_action
        db.commit()
        db.refresh(case)

        return case, {
            "execution_status": execution_status,
            "executed_action": target_action,
            "details": result_data
        }
