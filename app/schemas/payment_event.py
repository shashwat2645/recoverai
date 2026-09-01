from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class PaymentEventCreate(BaseModel):
    event_id: str
    event_type: str
    amount: float
    currency: str = "INR"
    customer_email: EmailStr
    customer_phone: str | None = None
    failure_reason: str | None = None
    raw_payload: dict


class PaymentEventResponse(BaseModel):
    id: str
    merchant_id: str
    event_id: str
    event_type: str
    amount: float
    currency: str
    customer_email: str
    customer_phone: str | None = None
    failure_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulateEventRequest(BaseModel):
    event_type: str = "payment.failed"
    amount: float = 1499.00
    currency: str = "INR"
    customer_email: EmailStr = "customer@example.com"
    customer_phone: str | None = "+919876543210"
    failure_reason: str | None = "BAD_REQUEST_PAYMENT_TIMED_OUT"


class WebhookIngestResponse(BaseModel):
    status: str = "success"
    message: str
    event_id: str
    is_duplicate: bool
