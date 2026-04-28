from fastapi import APIRouter

from app.modules.kriteria.schemas import KriteriaCreate, KriteriaUpdate
from app.modules.kriteria import service

router = APIRouter()


@router.get("")
def ambil_kriteria():
    return service.gas_ambil_semua_kriteria()


@router.get("/{kriteria_id}")
def ambil_detail_kriteria(kriteria_id: str):
    return service.gas_ambil_detail_kriteria(kriteria_id)


@router.post("")
def tambah_kriteria(payload: KriteriaCreate):
    return service.gas_bikin_kriteria(payload)


@router.put("/{kriteria_id}")
def ubah_kriteria(kriteria_id: str, payload: KriteriaUpdate):
    return service.gas_update_kriteria(kriteria_id, payload)


@router.delete("/{kriteria_id}")
def hapus_kriteria(kriteria_id: str):
    return service.gas_hapus_kriteria(kriteria_id)