from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_merchant
from app.models.merchant import Merchant
from app.schemas.dashboard import DashboardMetricsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["Dashboard Metrics"])


@router.get("/metrics", response_model=DashboardMetricsResponse, summary="Get Revenue Recovery Evaluation Metrics")
def get_dashboard_metrics(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated recovery metrics for the authenticated merchant:
    Total Failed Payments Analyzed, Revenue at Risk, Recovered Revenue,
    Success Rate %, Recovery Attempts, False Actions Avoided, and Case Status Breakdown.
    """
    return DashboardService.get_merchant_metrics(db, current_merchant.id)
