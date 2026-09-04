import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.api.v1 import api_v1_router
from app.core.database import Base, engine
import app.models  # Ensure all models are registered with Base.metadata

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Ensures all database tables exist on server startup.
    """
    Base.metadata.create_all(bind=engine)
    yield


def create_application() -> FastAPI:
    """
    Application factory pattern for FastAPI application initialization.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Autonomous Revenue Recovery Agent for Merchants — Razorpay AI Buildathon",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Static Files
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Include API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", summary="Dashboard UI", tags=["UI"])
    def get_dashboard():
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": f"Welcome to {settings.PROJECT_NAME}", "docs": "/docs"}

    @app.get("/dashboard", summary="Dashboard UI Alias", tags=["UI"])
    def get_dashboard_alias():
        return get_dashboard()

    @app.get("/login", summary="Merchant Login Portal", tags=["UI"])
    @app.get("/register", summary="Merchant Registration Portal", tags=["UI"])
    def get_auth_portal():
        return get_dashboard()

    return app


app = create_application()
