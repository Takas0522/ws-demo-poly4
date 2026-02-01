"""サービス設定サービス - メインアプリケーション"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from azure.cosmos.aio import CosmosClient

from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def init_cosmos_db(app: FastAPI) -> None:
    """Cosmos DB初期化"""
    try:
        settings.validate()

        cosmos_client = CosmosClient.from_connection_string(
            settings.COSMOS_DB_CONNECTION_STRING
        )

        database = cosmos_client.get_database_client(settings.COSMOS_DB_DATABASE_NAME)

        cosmos_container = database.get_container_client(
            settings.COSMOS_DB_CONTAINER_NAME
        )

        app.state.cosmos_client = cosmos_client
        app.state.cosmos_container = cosmos_container

        logger.info("Cosmos DB initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB: {e}")
        raise


async def cleanup_cosmos_db(app: FastAPI) -> None:
    """Cosmos DBクリーンアップ"""
    if hasattr(app.state, "cosmos_client"):
        await app.state.cosmos_client.close()
        logger.info("Cosmos DB connection closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("Starting service setting service...")
    await init_cosmos_db(app)
    yield
    logger.info("Shutting down service setting service...")
    await cleanup_cosmos_db(app)


app = FastAPI(
    title="Service Setting Service",
    description="マルチテナント管理アプリケーション - サービス設定サービス",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
from app.api import services, service_assignments

app.include_router(services.router)
app.include_router(service_assignments.router)


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
