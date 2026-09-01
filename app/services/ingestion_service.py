from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment_event import PaymentEvent
from app.schemas.payment_event import PaymentEventCreate
from app.services.risk_service import RiskService


def get_event_by_event_id(db: Session, event_id: str) -> PaymentEvent | None:
    """
    Fetch payment event by unique Razorpay event_id.
    """
    stmt = select(PaymentEvent).where(PaymentEvent.event_id == event_id)
    return db.execute(stmt).scalar_one_or_none()


def ingest_payment_event(
    db: Session,
    merchant_id: str,
    event_in: PaymentEventCreate
) -> tuple[PaymentEvent, bool]:
    """
    Idempotently ingests a payment failure event into the database and triggers risk detection.
    Returns tuple of (PaymentEvent, is_duplicate).
    """
    existing_event = get_event_by_event_id(db, event_in.event_id)
    if existing_event:
        return existing_event, True

    db_event = PaymentEvent(
        merchant_id=merchant_id,
        event_id=event_in.event_id,
        event_type=event_in.event_type,
        amount=event_in.amount,
        currency=event_in.currency,
        customer_email=event_in.customer_email,
        customer_phone=event_in.customer_phone,
        failure_reason=event_in.failure_reason,
        raw_payload=event_in.raw_payload
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Automatically trigger revenue risk detection & case initialization
    RiskService.detect_and_create_recovery_case(db, merchant_id, db_event)

    return db_event, False
