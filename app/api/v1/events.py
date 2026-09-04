import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.payment_event import SimulateEventRequest, PaymentEventResponse, PaymentEventCreate
from app.services.ingestion_service import ingest_payment_event

router = APIRouter(tags=["Payment Events"])


@router.post("/simulate", response_model=PaymentEventResponse, status_code=status.HTTP_201_CREATED, summary="Simulate Payment Failure Event")
def simulate_payment_failure(
    sim_in: SimulateEventRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Ingests a payment failure event for real-time risk assessment, AI root-cause analysis, and recovery orchestration.
    Ingests event under the current authenticated merchant's account.
    """
    generated_event_id = f"sim_evt_{uuid.uuid4().hex[:12]}"
    raw_sim_payload = {
        "event": sim_in.event_type,
        "simulated": True,
        "payload": {
            "payment": {
                "entity": {
                    "id": generated_event_id,
                    "amount": int(sim_in.amount * 100),
                    "currency": sim_in.currency,
                    "email": sim_in.customer_email,
                    "contact": sim_in.customer_phone,
                    "error_code": sim_in.failure_reason
                }
            }
        }
    }

    event_in = PaymentEventCreate(
        event_id=generated_event_id,
        event_type=sim_in.event_type,
        amount=sim_in.amount,
        currency=sim_in.currency,
        customer_email=sim_in.customer_email,
        customer_phone=sim_in.customer_phone,
        failure_reason=sim_in.failure_reason,
        raw_payload=raw_sim_payload
    )

    db_event, _ = ingest_payment_event(db, current_merchant.id, event_in)
    return db_event
