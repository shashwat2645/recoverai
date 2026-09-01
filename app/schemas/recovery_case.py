from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RecoveryCaseResponse(BaseModel):
    id: str
    merchant_id: str
    payment_event_id: str
    status: str
    risk_score: float
    amount_at_risk: float
    customer_name: str | None = None
    customer_email: str
    recovery_attempts: int
    max_allowed_attempts: int
    last_action_taken: str | None = None
    next_retry_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryCaseListResponse(BaseModel):
    total: int
    cases: list[RecoveryCaseResponse]
