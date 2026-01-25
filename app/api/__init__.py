"""API router initialization."""
from fastapi import APIRouter

from app.api.endpoints import health

api_router = APIRouter()

# Include health check endpoint (no /api prefix)
api_router.include_router(health.router, tags=["Health"])
