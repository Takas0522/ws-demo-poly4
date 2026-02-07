from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.api.v1 import health, tenants

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="テナント管理サービス",
    description="テナント・テナントユーザー管理API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(tenants.router, prefix="/api/v1", tags=["Tenants"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name} on port {settings.port}")
    logger.info(f"Cosmos DB Endpoint: {settings.cosmos_db_endpoint}")
    logger.info(f"Database: {settings.cosmos_db_database}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")
