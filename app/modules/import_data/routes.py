from fastapi import APIRouter, File, UploadFile

from app.modules.import_data import service
from app.modules.import_data.schemas import MappingImportRequest


router = APIRouter()


@router.post("/preview")
async def preview_dataset(file: UploadFile = File(...)):
    return await service.gas_preview_dataset(file)


@router.post("/save-raw")
async def save_raw_dataset(file: UploadFile = File(...)):
    return await service.gas_simpan_raw_dataset(file=file)


@router.get("/batch")
def get_import_batch():
    return service.gas_ambil_import_batch()


@router.get("/batches")
def get_import_batches():
    return service.gas_ambil_import_batch()


@router.post("/map-to-keluarga")
def map_import_dataset_to_keluarga(payload: MappingImportRequest):
    return service.gas_proses_import_keluarga_dan_penilaian(payload)


@router.post("/mapping-to-keluarga")
def mapping_import_dataset_to_keluarga(payload: MappingImportRequest):
    return service.gas_proses_import_keluarga_dan_penilaian(payload)