from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(tags=["Audit Logs"])


@router.get("", response_model=AuditLogListResponse, summary="List Merchant Global Audit Logs")
def list_merchant_audit_logs(
    limit: int = Query(50, ge=1, le=200, description="Max audit logs to retrieve"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Retrieves global chronological audit trail entries for the authenticated merchant.
    """
    logs = AuditService.get_merchant_audit_logs(db, current_merchant.id, limit=limit)
    return AuditLogListResponse(total=len(logs), audit_logs=logs)
