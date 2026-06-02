from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from src.config import settings
from src.database.session import async_engine
from src.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    yield
    logger.info("Shutting down application...")
    await async_engine.dispose()


app = FastAPI(
    title="ClarityDoc API",
    description="Document management and analysis platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
