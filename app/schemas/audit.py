from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: str
    recovery_case_id: str
    merchant_id: str
    event_type: str
    prompt_context: dict | None = None
    ai_reasoning: str | None = None
    confidence_score: float | None = None
    recommended_action: str
    executed_action: str | None = None
    execution_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    total: int
    audit_logs: list[AuditLogResponse]
