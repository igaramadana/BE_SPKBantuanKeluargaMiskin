from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.modules.health.routes import router as health_router
from app.modules.kriteria.routes import router as kriteria_router
from app.modules.keluarga.routes import router as keluarga_router
from app.modules.ahp.routes import router as ahp_router
from app.modules.saw.routes import router as saw_router
from app.modules.import_data.routes import router as import_data_router
from app.modules.public.routes import router as public_router

app = FastAPI(
    title="API SPK Bantuan Keluarga Miskin",
    version="1.0.0",
)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if getattr(settings, "FRONTEND_URL", None):
    allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "API SPK Bantuan Keluarga Miskin berjalan.",
        "docs": "/docs",
        "health": "/api/health",
    }


app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(kriteria_router, prefix="/api/kriteria", tags=["Kriteria"])
app.include_router(keluarga_router, prefix="/api/keluarga", tags=["Keluarga"])
app.include_router(ahp_router, prefix="/api/ahp", tags=["AHP"])
app.include_router(saw_router, prefix="/api/saw", tags=["SAW"])
app.include_router(import_data_router, prefix="/api/import", tags=["Import Data"])
app.include_router(public_router, prefix="/api/public", tags=["Public"])