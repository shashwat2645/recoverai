import json
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.core.database import get_db
from app.core.webhook_security import verify_razorpay_signature
from app.models.merchant import Merchant
from app.schemas.payment_event import PaymentEventCreate, WebhookIngestResponse
from app.services.ingestion_service import ingest_payment_event

router = APIRouter(tags=["Webhooks"])


@router.post("/razorpay", response_model=WebhookIngestResponse, summary="Razorpay Webhook Endpoint")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Receives and processes incoming Razorpay webhook payment failure events.
    Verifies HMAC SHA-256 signature and ingests events idempotently.
    """
    raw_body = await request.body()

    # Verify HMAC signature if webhook secret is configured
    if settings.RAZORPAY_WEBHOOK_SECRET and settings.RAZORPAY_WEBHOOK_SECRET != "dummy_webhook_secret":
        if not x_razorpay_signature or not verify_razorpay_signature(raw_body, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Razorpay-Signature header."
            )

    try:
        payload = json.loads(raw_body.decode('utf-8'))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload format."
        )

    # Extract event attributes from standard Razorpay payload structure
    event_type = payload.get("event", "payment.failed")
    event_id = payload.get("account_id", "") + "_" + str(payload.get("created_at", "")) + "_" + str(hash(raw_body))
    
    payment_entity = {}
    if "payload" in payload and "payment" in payload["payload"]:
        payment_entity = payload["payload"]["payment"]["entity"]
        event_id = payload["payload"]["payment"]["entity"].get("id", event_id)

    amount = payment_entity.get("amount", 0)
    # Convert paise to INR if necessary (Razorpay amounts are in paise)
    if amount > 0 and payment_entity.get("currency") == "INR":
        amount = amount / 100.0

    email = payment_entity.get("email", "unknown@customer.com")
    phone = payment_entity.get("contact", None)
    error_code = payment_entity.get("error_code") or payment_entity.get("error_description") or "PAYMENT_FAILED"

    # Find merchant account context
    merchant = db.execute(select(Merchant).where(Merchant.is_active == True)).scalars().first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active merchant registered in system to attach webhook event."
        )

    event_in = PaymentEventCreate(
        event_id=event_id,
        event_type=event_type,
        amount=amount,
        currency=payment_entity.get("currency", "INR"),
        customer_email=email,
        customer_phone=phone,
        failure_reason=error_code,
        raw_payload=payload
    )

    db_event, is_duplicate = ingest_payment_event(db, merchant.id, event_in)

    return WebhookIngestResponse(
        status="success",
        message="Duplicate event ignored" if is_duplicate else "Payment failure event ingested successfully",
        event_id=db_event.event_id,
        is_duplicate=is_duplicate
    )
