from fastapi import APIRouter
from app.modules.saw.schemas import (
    SawCalculateRequest,
    SawFromDatabaseRequest,
    SimpanPenilaianRequest,
)
from app.modules.saw import service

router = APIRouter()


@router.post("/calculate")
def hitung_saw_manual(payload: SawCalculateRequest):
    return service.gas_hitung_manual(payload)


@router.post("/penilaian")
def simpan_penilaian(payload: SimpanPenilaianRequest):
    return service.gas_simpan_penilaian(payload)


@router.post("/calculate-from-db")
def hitung_saw_dari_database(payload: SawFromDatabaseRequest):
    return service.gas_hitung_dari_database(payload)


@router.get("/hasil/latest")
def ambil_hasil_terbaru():
    return service.gas_ambil_hasil_terbaru()


@router.get("/riwayat")
def ambil_riwayat_perhitungan():
    return service.gas_ambil_riwayat()


@router.get("/riwayat/{riwayat_id}/hasil")
def ambil_hasil_riwayat(riwayat_id: str):
    return service.gas_ambil_hasil_by_riwayat(riwayat_id)