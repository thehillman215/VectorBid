"""
FastAPI application factory for VectorBid
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.api.fastapi_routes import router as api_router


def create_fastapi_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="VectorBid API",
        description="AI-powered pilot schedule bidding assistant",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent

    # Mount static files
    static_folder = project_root / "src" / "ui" / "static"
    if static_folder.exists():
        app.mount("/static", StaticFiles(directory=str(static_folder)), name="static")

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "VectorBid FastAPI",
            "version": "1.0.0"
        }

    # Include existing FastAPI components
    try:
        from app.compat.validate_router import router as validate_router
        app.include_router(validate_router, prefix="/api")
        print("✅ Validation router registered!")
    except ImportError as e:
        print(f"⚠️ Validation router not available: {e}")

    return app