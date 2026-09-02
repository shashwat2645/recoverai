from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.ai_agent import TestAIReasoningRequest, AIReasoningResult
from app.services.gemini_service import GeminiService

router = APIRouter(tags=["AI Reasoning Agent"])


@router.post("/test-reasoning", response_model=AIReasoningResult, status_code=status.HTTP_200_OK, summary="Test Gemini AI Reasoning Agent")
def test_ai_reasoning_endpoint(
    request_in: TestAIReasoningRequest,
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Invokes Google Gemini AI reasoning on a given payment failure context and returns structured recommendations.
    """
    result = GeminiService.analyze_payment_failure(
        failure_reason=request_in.failure_reason,
        amount=request_in.amount,
        customer_email=request_in.customer_email,
        policy_context=request_in.policy_context
    )
    return result
