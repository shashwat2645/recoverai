from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.recovery_case import RecoveryCase, RecoveryStatus
from app.models.payment_event import PaymentEvent
from app.schemas.ai_agent import AIReasoningResult
from app.services.gemini_service import GeminiService
from app.services.rag_service import RAGService


class AgentService:
    @classmethod
    def analyze_and_recommend(
        cls,
        db: Session,
        case_id: str,
        merchant_id: str,
        policy_context_override: str | None = None
    ) -> tuple[RecoveryCase, AIReasoningResult]:
        """
        Orchestrates the AI Recovery Agent decision workflow for a recovery case.
        Enforces stopping rules, retrieves merchant RAG policy context, and determines bounded actions.
        """
        stmt = select(RecoveryCase).where(
            RecoveryCase.id == case_id,
            RecoveryCase.merchant_id == merchant_id
        )
        case = db.execute(stmt).scalar_one_or_none()

        if not case:
            raise ValueError(f"Recovery case with ID {case_id} not found for merchant.")

        # 1. Enforce Merchant Stopping Rule Guardrail: Max Retry Attempts
        if case.recovery_attempts >= case.max_allowed_attempts:
            case.status = RecoveryStatus.FAILED.value
            case.last_action_taken = "MARK_UNRECOVERABLE"
            db.commit()
            db.refresh(case)

            stopping_reasoning = AIReasoningResult(
                root_cause="Maximum allowed recovery attempts reached.",
                recommended_action="MARK_UNRECOVERABLE",
                confidence_score=0.99,
                explanation=f"Stopping rule enforced: case has already reached maximum limit of {case.max_allowed_attempts} attempts.",
                stopping_rules_triggered=["MAX_RETRIES_EXCEEDED"]
            )
            return case, stopping_reasoning

        # 2. Transition case state to ANALYZING
        case.status = RecoveryStatus.ANALYZING.value
        db.commit()

        # 3. Fetch linked PaymentEvent for failure context
        event_stmt = select(PaymentEvent).where(PaymentEvent.id == case.payment_event_id)
        payment_event = db.execute(event_stmt).scalar_one()

        # 4. Perform Semantic RAG Retrieval for Merchant Policies
        if policy_context_override:
            policy_context = policy_context_override
        else:
            search_query = f"{payment_event.failure_reason} payment retry discount policy"
            policy_context = RAGService.get_relevant_policy_context(db, merchant_id, search_query)

        # 5. Invoke Gemini AI Reasoning Engine with RAG Context
        reasoning_result = GeminiService.analyze_payment_failure(
            failure_reason=payment_event.failure_reason,
            amount=case.amount_at_risk,
            customer_email=case.customer_email,
            policy_context=policy_context,
            recovery_attempts=case.recovery_attempts
        )

        # 6. Update RecoveryCase with AI recommendations
        case.status = RecoveryStatus.ACTION_REQUIRED.value
        case.last_action_taken = reasoning_result.recommended_action
        db.commit()
        db.refresh(case)

        return case, reasoning_result
