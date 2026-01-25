"""Health check API endpoints."""
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.database import get_db_client

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=Dict,
    tags=["Health"],
    summary="Health check endpoint",
    description="Check the health status of the service and its dependencies",
)
async def health_check() -> Dict:
    """
    Health check endpoint.
    
    Returns service status and dependency health information.
    
    Returns:
        Dict: Health status information including service name, version, 
              timestamp, and dependency statuses
    """
    db_client = get_db_client()
    
    # Check database connection
    db_healthy = await db_client.health_check()
    
    # Determine overall status
    overall_status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dependencies": {
            "cosmosdb": {
                "status": "healthy" if db_healthy else "unhealthy",
                "database": settings.cosmosdb_database,
            }
        },
    }
