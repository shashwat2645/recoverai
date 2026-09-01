from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery_case import RecoveryCaseResponse, RecoveryCaseListResponse

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
