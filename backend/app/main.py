import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MindTrack API...")
    await create_tables()
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down MindTrack API...")


app = FastAPI(
    title="MindTrack API",
    description="Smart Mood Diary with AI-powered insights",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.endpoints.auth import router as auth_router  # noqa: E402
from app.api.endpoints.entries import router as entries_router  # noqa: E402
from app.api.endpoints.analytics import router as analytics_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(entries_router, prefix="/api/v1/entries", tags=["Entries"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
