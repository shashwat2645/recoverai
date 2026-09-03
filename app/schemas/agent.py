from pydantic import BaseModel, ConfigDict
from app.schemas.ai_agent import AIReasoningResult


class AgentAnalysisResponse(BaseModel):
    case_id: str
    merchant_id: str
    status: str
    risk_score: float
    amount_at_risk: float
    reasoning: AIReasoningResult

    model_config = ConfigDict(from_attributes=True)
