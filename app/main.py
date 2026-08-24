from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_v1_router


def create_application() -> FastAPI:
    """
    Application factory pattern for FastAPI application initialization.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Autonomous Revenue Recovery Agent for Merchants — Razorpay AI Buildathon",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production environment
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", summary="Root Health Endpoint", tags=["Root"])
    def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health"
        }

    return app


app = create_application()
