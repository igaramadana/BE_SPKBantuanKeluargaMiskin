from fastapi import APIRouter

from app.modules.kriteria import service
from app.modules.kriteria.schemas import (
    KriteriaCreateRequest,
    KriteriaUpdateRequest,
)


router = APIRouter()


@router.get("")
def get_all_kriteria():
    return service.gas_ambil_semua_kriteria()


@router.get("/{kriteria_id}")
def get_detail_kriteria(kriteria_id: str):
    return service.gas_ambil_kriteria_detail(kriteria_id)


@router.post("")
def create_kriteria(payload: KriteriaCreateRequest):
    return service.gas_tambah_kriteria(payload)


@router.patch("/{kriteria_id}")
def patch_kriteria(kriteria_id: str, payload: KriteriaUpdateRequest):
    return service.gas_update_kriteria(kriteria_id, payload)


@router.delete("/{kriteria_id}")
def delete_kriteria(kriteria_id: str):
    return service.gas_hapus_kriteria(kriteria_id)