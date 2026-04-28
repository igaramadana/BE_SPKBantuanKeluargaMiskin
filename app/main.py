from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.health.routes import router as health_router
from app.modules.kriteria.routes import router as kriteria_router
from app.modules.keluarga.routes import router as keluarga_router
from app.modules.ahp.routes import router as ahp_router
from app.modules.saw.routes import router as saw_router

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
app.include_router(kriteria_router, prefix="/api/kriteria", tags=["Kriteria"])
app.include_router(keluarga_router, prefix="/api/keluarga", tags=["Keluarga"])
app.include_router(ahp_router, prefix="/api/ahp", tags=["AHP"])
app.include_router(saw_router, prefix="/api/saw", tags=["SAW"])