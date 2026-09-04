from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.webhooks import router as webhook_router
from app.api.v1.events import router as events_router
from app.api.v1.razorpay_gateway import router as razorpay_router
from app.api.v1.cases import router as cases_router
from app.api.v1.ai import router as ai_router
from app.api.v1.policies import router as policies_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(webhook_router, prefix="/webhooks")
api_v1_router.include_router(events_router, prefix="/events")
api_v1_router.include_router(razorpay_router, prefix="/razorpay")
api_v1_router.include_router(cases_router, prefix="/cases")
api_v1_router.include_router(ai_router, prefix="/ai")
api_v1_router.include_router(policies_router, prefix="/policies")
api_v1_router.include_router(audit_router, prefix="/audit-logs")
api_v1_router.include_router(dashboard_router, prefix="/dashboard")
