from pydantic import BaseModel, Field, EmailStr


class AIReasoningResult(BaseModel):
    root_cause: str = Field(..., description="Diagnosis of why the payment failed based on code and context.")
    recommended_action: str = Field(
        ...,
        description="Allowed bounded recovery action: GENERATE_PAYMENT_LINK, SEND_REMINDER, SCHEDULE_RETRY, or MARK_UNRECOVERABLE"
    )
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    explanation: str = Field(..., description="Human-readable explanation of why this action was selected.")
    stopping_rules_triggered: list[str] = Field(
        default_factory=list,
        description="Flags if any merchant stopping rules were triggered (e.g. MAX_RETRIES_EXCEEDED)."
    )


class TestAIReasoningRequest(BaseModel):
    failure_reason: str = "BAD_REQUEST_PAYMENT_TIMED_OUT"
    amount: float = 1499.00
    customer_email: EmailStr = "customer@example.com"
    policy_context: str | None = "Merchant Policy: Retries allowed up to 3 times within 72 hours. Send instant payment link."
