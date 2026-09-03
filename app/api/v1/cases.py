from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery_case import RecoveryCaseResponse, RecoveryCaseListResponse
from app.schemas.agent import AgentAnalysisResponse
from app.schemas.executor import ActionExecutionRequest, ActionExecutionResponse
from app.services.agent_service import AgentService
from app.services.executor_service import ActionExecutorService

router = APIRouter(tags=["Recovery Cases"])


@router.get("", response_model=RecoveryCaseListResponse, summary="List Merchant Recovery Cases")
def list_recovery_cases(
    status_filter: str | None = Query(None, alias="status", description="Filter cases by status"),
    min_risk: float | None = Query(None, description="Filter cases by minimum risk score"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Lists all recovery cases belonging to the authenticated merchant with optional status and risk filters.
    """
    query = select(RecoveryCase).where(RecoveryCase.merchant_id == current_merchant.id)

    if status_filter:
        query = query.where(RecoveryCase.status == status_filter.upper())
    if min_risk is not None:
        query = query.where(RecoveryCase.risk_score >= min_risk)

    query = query.order_by(RecoveryCase.created_at.desc())

    cases = db.execute(query).scalars().all()
    return RecoveryCaseListResponse(total=len(cases), cases=cases)


@router.get("/{case_id}", response_model=RecoveryCaseResponse, summary="Get Single Recovery Case Details")
def get_recovery_case(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Retrieves details for a specific recovery case. Enforces multi-tenant ownership check.
    """
    stmt = select(RecoveryCase).where(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    )
    case = db.execute(stmt).scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    return case


@router.post("/{case_id}/analyze", response_model=AgentAnalysisResponse, summary="Run AI Recovery Agent Analysis on Case")
def analyze_recovery_case(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Triggers the AI Recovery Agent to analyze a specific recovery case and output recommendations.
    """
    try:
        case, reasoning = AgentService.analyze_and_recommend(db, case_id, current_merchant.id)
        return AgentAnalysisResponse(
            case_id=case.id,
            merchant_id=case.merchant_id,
            status=case.status,
            risk_score=case.risk_score,
            amount_at_risk=case.amount_at_risk,
            reasoning=reasoning
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{case_id}/execute", response_model=ActionExecutionResponse, summary="Execute Bounded Action on Case")
def execute_recovery_case_action(
    case_id: str,
    exec_in: ActionExecutionRequest | None = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Executes a bounded recovery action (e.g. generating Razorpay Payment Link or sending reminder) on a case.
    Enforces strict guardrail checks blocking unallowed financial operations (e.g., refunds).
    """
    action_override = exec_in.action_override if exec_in else None
    try:
        case, result = ActionExecutorService.execute_action(
            db=db,
            case_id=case_id,
            merchant_id=current_merchant.id,
            action_override=action_override
        )
        return ActionExecutionResponse(
            case_id=case.id,
            merchant_id=case.merchant_id,
            status=case.status,
            executed_action=result["executed_action"],
            execution_status=result["execution_status"],
            details=result["details"]
        )
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe)
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
