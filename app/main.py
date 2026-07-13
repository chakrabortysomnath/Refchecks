"""
FastAPI application entry point.
Initializes the API, configures middleware, and sets up routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import create_all_tables
from app.routes import (
    auth, competitions, matches, bias, statistics, admin, favourability
)


# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ===== LIFESPAN EVENTS =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    Startup: Create database tables
    Shutdown: Clean up resources
    """
    # Startup
    logger.info("🚀 RefChecks API Starting...")
    try:
        create_all_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 RefChecks API Shutting Down...")


# ===== FASTAPI APP INITIALIZATION =====

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)


# ===== CORS MIDDLEWARE =====

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ===== HEALTH CHECK ENDPOINT =====

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used by Render to verify the service is running.
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "api_version": settings.api_version,
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RefChecks Football Bias Analysis API",
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "health": "/health",
    }


# ===== INCLUDE ROUTERS =====

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}},
)

app.include_router(
    competitions.router,
    prefix="/api",
    tags=["Competitions"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    matches.router,
    prefix="/api",
    tags=["Matches"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    bias.router,
    prefix="/api",
    tags=["Bias Analysis"],
    responses={400: {"description": "Invalid parameters"}},
)

app.include_router(
    statistics.router,
    prefix="/api",
    tags=["Statistics & Visualization"],
    responses={400: {"description": "Invalid parameters"}},
)

app.include_router(
    favourability.router,
    prefix="/api",
    tags=["Favourability"],
    responses={400: {"description": "Invalid parameters"}},
)

app.include_router(
    admin.router,
    prefix="/api",
    tags=["Admin - Temporary Setup"],
    responses={403: {"description": "Invalid setup key"}},
)


# ===== STARTUP MESSAGE =====

@app.on_event("startup")
async def startup_event():
    logger.info(f"🔧 Running in {settings.environment} mode")
    logger.info(f"📊 Statsbomb data source: {settings.statsbomb_data_repo}")
    logger.info(f"🔐 CORS origins: {settings.cors_origins_list}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level="info",
    )
