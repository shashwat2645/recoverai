import json
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.ai_agent import AIReasoningResult


class GeminiService:
    @staticmethod
    def _get_client() -> genai.Client | None:
        """
        Initializes the official Google GenAI SDK Client if a valid GEMINI_API_KEY is configured.
        """
        key = settings.GEMINI_API_KEY
        if key and key != "dummy_key_for_setup" and key != "your_gemini_api_key_from_google_ai_studio":
            try:
                return genai.Client(api_key=key)
            except Exception as e:
                print(f"[Gemini API Notice]: Client initialization failed: {e}")
        return None

    @classmethod
    def analyze_payment_failure(
        cls,
        failure_reason: str,
        amount: float,
        customer_email: str,
        policy_context: str | None = None,
        recovery_attempts: int = 0
    ) -> AIReasoningResult:
        """
        Uses Google Gemini AI to analyze root cause of payment failure, evaluate merchant policies,
        and output structured recovery recommendations.
        """
        client = cls._get_client()

        system_instruction = (
            "You are an autonomous AI Revenue Recovery Specialist for online merchants. "
            "Your task is to analyze payment failure events, evaluate merchant policies, "
            "diagnose the root cause, assess confidence, and recommend a single bounded action. "
            "Allowed actions strictly are: GENERATE_PAYMENT_LINK, SEND_REMINDER, SCHEDULE_RETRY, or MARK_UNRECOVERABLE. "
            "You must NEVER recommend refunds or altering amounts."
        )

        user_prompt = f"""
Analyze the following payment failure context:
- Failure Reason / Code: {failure_reason}
- Transaction Amount: ₹{amount:.2f}
- Customer Email: {customer_email}
- Previous Recovery Attempts: {recovery_attempts}
- Merchant Policy Context: {policy_context or 'Standard retry policy: Max 3 retries. Generate payment link for transient failures.'}

Respond strictly matching the requested JSON structure.
"""

        if client:
            try:
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=AIReasoningResult,
                        temperature=0.1
                    )
                )

                if response.text:
                    parsed_json = json.loads(response.text)
                    return AIReasoningResult(**parsed_json)
            except Exception as e:
                print(f"[Gemini API Notice]: Live AI generation failed: {e}. Falling back to deterministic AI model engine.")

        # Deterministic fallback AI reasoning engine (when running offline or without API key)
        reason_upper = (failure_reason or "").upper()

        if recovery_attempts >= 3:
            return AIReasoningResult(
                root_cause="Maximum recovery attempts reached.",
                recommended_action="MARK_UNRECOVERABLE",
                confidence_score=0.98,
                explanation="Merchant stopping rule triggered: case exceeded maximum retry threshold of 3 attempts.",
                stopping_rules_triggered=["MAX_RETRIES_EXCEEDED"]
            )

        if "TIMED_OUT" in reason_upper or "GATEWAY_ERROR" in reason_upper or "NETWORK" in reason_upper:
            return AIReasoningResult(
                root_cause="Transient bank gateway network latency during transaction processing.",
                recommended_action="GENERATE_PAYMENT_LINK",
                confidence_score=0.92,
                explanation="High probability of customer conversion via instant Razorpay payment retry link.",
                stopping_rules_triggered=[]
            )

        if "INSUFFICIENT" in reason_upper or "DECLINED" in reason_upper:
            return AIReasoningResult(
                root_cause="Customer account liquidity or daily transaction limit reached.",
                recommended_action="SEND_REMINDER",
                confidence_score=0.84,
                explanation="Send polite payment reminder notice to customer before attempting automated retry.",
                stopping_rules_triggered=[]
            )

        if "EXPIRED" in reason_upper or "INVALID" in reason_upper:
            return AIReasoningResult(
                root_cause="Expired payment instrument or invalid account credentials.",
                recommended_action="MARK_UNRECOVERABLE",
                confidence_score=0.95,
                explanation="Instrument is permanently invalid; requires customer manual account update.",
                stopping_rules_triggered=["PERMANENT_INSTRUMENT_FAILURE"]
            )

        return AIReasoningResult(
            root_cause="Unclassified payment gateway processing error.",
            recommended_action="SCHEDULE_RETRY",
            confidence_score=0.70,
            explanation="Schedule automated retry in 24 hours per standard merchant recovery guidelines.",
            stopping_rules_triggered=[]
        )
