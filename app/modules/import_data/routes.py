from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.modules.import_data.schemas import MappingKolomRequest
from app.modules.import_data import service

router = APIRouter()


@router.post("/preview")
async def preview_import(file: UploadFile = File(...)):
    return service.intip_file(file)


@router.post("/save-raw")
async def save_raw_import(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(default=None),
):
    return service.gas_simpan_raw_import(
        file=file,
        uploaded_by=uploaded_by,
    )


@router.get("/batches")
def ambil_semua_import_batch():
    return service.gas_ambil_semua_batch()


@router.get("/batches/{import_batch_id}")
def ambil_detail_import_batch(import_batch_id: str):
    return service.gas_ambil_detail_batch(import_batch_id)


@router.post("/map-to-keluarga")
def mapping_import_ke_keluarga(payload: MappingKolomRequest):
    return service.gas_mapping_ke_keluarga(payload)