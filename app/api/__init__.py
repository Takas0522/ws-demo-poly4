"""API router initialization."""
from fastapi import APIRouter

from app.api.endpoints import health, services

api_router = APIRouter()

# Include health check endpoint (no /api prefix)
api_router.include_router(health.router, tags=["Health"])

# Include services endpoints with /api prefix
api_router.include_router(services.router, prefix="/api", tags=["Services"])
