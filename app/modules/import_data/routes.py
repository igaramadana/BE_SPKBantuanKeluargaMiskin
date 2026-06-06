from fastapi import APIRouter, File, UploadFile

from app.modules.import_data import service
from app.modules.import_data.schemas import (
    AutoGeneratePenilaianRequest,
    MappingImportRequest,
)


router = APIRouter()


@router.post("/preview")
async def preview_import_dataset(file: UploadFile = File(...)):
    return await service.gas_preview_import(file)


@router.post("/save-raw")
async def save_raw_import_dataset(file: UploadFile = File(...)):
    return await service.gas_simpan_raw_import(file)


@router.get("/batches")
def get_import_batches():
    return service.gas_ambil_import_batch()


@router.get("/batch/{import_batch_id}")
def get_import_batch(import_batch_id: str):
    return service.gas_ambil_import_batch_by_id(import_batch_id)


@router.post("/auto-generate-penilaian")
def auto_generate_penilaian(payload: AutoGeneratePenilaianRequest):
    return service.gas_auto_generate_penilaian(payload)


# Backward compatibility endpoint lama.
@router.post("/map-to-keluarga")
def map_import_to_keluarga(payload: MappingImportRequest):
    return service.gas_proses_import_keluarga_dan_penilaian(payload)


@router.post("/mapping-to-keluarga")
def mapping_import_to_keluarga(payload: MappingImportRequest):
    return service.gas_proses_import_keluarga_dan_penilaian(payload)