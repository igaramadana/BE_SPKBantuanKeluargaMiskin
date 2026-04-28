from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.health.routes import router as health_router

app = FastAPI(
    title="API SPK Bantuan Keluarga Miskin",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allo_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")