from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logger import logger
from app.routes.configuration_routes import router as config_router
from app.repositories.cosmos_client import cosmos_client
from app.repositories.cache_service import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Service Settings Service...")
    try:
        await cosmos_client.initialize()
        if cosmos_client._initialized:
            logger.info("✅ CosmosDB initialized successfully")
        else:
            logger.warning("❌ Warning: CosmosDB connection failed")
            logger.warning("   Please ensure CosmosDB Emulator is running")

        await cache_service.connect()
        logger.info("Service initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        logger.warning("Service will continue with limited functionality")

    yield

    # Shutdown
    logger.info("Shutting down Service Settings Service...")
    await cache_service.disconnect()
    logger.info("Service shutdown complete")


app = FastAPI(
    title="Service Settings Service",
    description="Microservice for managing application and tenant-specific configurations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "service-setting-service",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
