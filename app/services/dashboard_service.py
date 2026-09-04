from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.recovery_case import RecoveryCase, RecoveryStatus
from app.models.payment_event import PaymentEvent
from app.models.audit_log import AuditLog
from app.schemas.dashboard import DashboardMetricsResponse


class DashboardService:
    @classmethod
    def get_merchant_metrics(cls, db: Session, merchant_id: str) -> DashboardMetricsResponse:
        """
        Aggregates live performance metrics for merchant revenue recovery evaluation.
        """
        # 1. Total failed payments analyzed
        total_failed_stmt = select(func.count(PaymentEvent.id)).where(PaymentEvent.merchant_id == merchant_id)
        total_failed = db.execute(total_failed_stmt).scalar() or 0

        # 2. Total revenue at risk
        cases_stmt = select(RecoveryCase).where(RecoveryCase.merchant_id == merchant_id)
        cases = db.execute(cases_stmt).scalars().all()

        revenue_at_risk = sum(case.amount_at_risk for case in cases)

        # 3. Recovered cases and revenue
        recovered_cases = [c for c in cases if c.status == RecoveryStatus.RECOVERED.value]
        recovered_revenue = sum(c.amount_at_risk for c in recovered_cases)

        # 4. Total recovery attempts
        total_attempts = sum(c.recovery_attempts for c in cases)

        # 5. Success rate percentage
        if total_failed > 0:
            success_rate = round((len(recovered_cases) / total_failed) * 100, 1)
        else:
            success_rate = 0.0

        # 6. False actions avoided (blocked by guardrails)
        guardrail_stmt = select(func.count(AuditLog.id)).where(
            AuditLog.merchant_id == merchant_id,
            AuditLog.execution_status == "BLOCKED_BY_GUARDRAIL"
        )
        false_actions_avoided = db.execute(guardrail_stmt).scalar() or 0

        # 7. Active cases (cases still in pipeline)
        active_statuses = {
            RecoveryStatus.DETECTED.value,
            RecoveryStatus.ANALYZING.value,
            RecoveryStatus.ACTION_REQUIRED.value,
            RecoveryStatus.RECOVERING.value
        }
        active_cases = sum(1 for c in cases if c.status in active_statuses)

        # 8. Status breakdown
        breakdown = {status.value: 0 for status in RecoveryStatus}
        for c in cases:
            if c.status in breakdown:
                breakdown[c.status] += 1

        return DashboardMetricsResponse(
            total_failed_payments=total_failed,
            revenue_at_risk=round(revenue_at_risk, 2),
            recovered_revenue=round(recovered_revenue, 2),
            recovery_attempts=total_attempts,
            recovery_success_rate_pct=success_rate,
            false_actions_avoided=false_actions_avoided,
            active_cases=active_cases,
            status_breakdown=breakdown
        )
