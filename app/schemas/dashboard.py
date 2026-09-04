from pydantic import BaseModel


class DashboardMetricsResponse(BaseModel):
    total_failed_payments: int
    revenue_at_risk: float
    recovered_revenue: float
    recovery_attempts: int
    recovery_success_rate_pct: float
    false_actions_avoided: int
    active_cases: int
    status_breakdown: dict[str, int]
