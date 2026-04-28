from fastapi import APIRouter
from app.modules.kriteria import KriteriaCreate
from app.modules.kriteria import service

router = APIRouter()

@router.get("")
def ambil_kriteria():
    return service.gas_ambil_semua_kriteria()

@router.post("")
def tambah_kriteria(payload: KriteriaCreate):
    return service.gas_bikin_kriteria(payload)