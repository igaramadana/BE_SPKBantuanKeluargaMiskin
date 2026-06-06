from fastapi import APIRouter

from app.modules.saw import service
from app.modules.saw.schemas import (
    AutoGeneratePenilaianImportRequest,
    SawCalculateFromDbRequest,
    SimpanPenilaianSawRequest,
)


router = APIRouter()


@router.post("/penilaian")
def simpan_penilaian_saw(payload: SimpanPenilaianSawRequest):
    return service.gas_simpan_penilaian(payload)


@router.post("/penilaian/auto-generate-from-import")
def auto_generate_penilaian_from_import(payload: AutoGeneratePenilaianImportRequest):
    return service.gas_auto_generate_penilaian_dari_import(
        import_batch_id=payload.import_batch_id
    )


@router.post("/calculate-from-db")
def calculate_saw_from_db(payload: SawCalculateFromDbRequest):
    return service.gas_hitung_dari_database(payload)


@router.get("/hasil/latest")
def get_hasil_saw_latest():
    return service.gas_ambil_hasil_terbaru()


@router.get("/hasil/riwayat/{riwayat_id}")
def get_hasil_saw_by_riwayat(riwayat_id: str):
    return service.gas_ambil_hasil_by_riwayat(riwayat_id)


@router.get("/riwayat")
def get_riwayat_saw():
    return service.gas_ambil_riwayat()