from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PolicyCreate(BaseModel):
    title: str
    policy_type: str = "GENERAL"  # REFUND, RETRY, DISCOUNT, GENERAL
    content: str


class PolicyResponse(BaseModel):
    id: str
    merchant_id: str
    title: str
    policy_type: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyListResponse(BaseModel):
    total: int
    policies: list[PolicyResponse]
