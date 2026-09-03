from pydantic import BaseModel, ConfigDict


class ActionExecutionRequest(BaseModel):
    action_override: str | None = None  # GENERATE_PAYMENT_LINK, SEND_REMINDER, SCHEDULE_RETRY, MARK_UNRECOVERABLE


class ActionExecutionResponse(BaseModel):
    case_id: str
    merchant_id: str
    status: str
    executed_action: str
    execution_status: str
    details: dict

    model_config = ConfigDict(from_attributes=True)
