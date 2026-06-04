from typing import Optional

from fastapi import APIRouter, Query

from app.modules.keluarga import service
from app.modules.keluarga.schemas import (
    KeluargaCreateRequest,
    KeluargaUpdateRequest,
    KeluargaVerifikasiRequest,
)


router = APIRouter()


@router.get("")
def get_all_keluarga(
    search: Optional[str] = Query(default=None),
    status_verifikasi: Optional[str] = Query(default=None),
    kelurahan: Optional[str] = Query(default=None),
    dusun: Optional[str] = Query(default=None),
):
    return service.gas_ambil_semua_keluarga(
        search=search,
        status_verifikasi=status_verifikasi,
        kelurahan=kelurahan,
        dusun=dusun,
    )


@router.get("/{keluarga_id}")
def get_detail_keluarga(keluarga_id: str):
    return service.gas_ambil_keluarga_detail(keluarga_id)


@router.post("")
def create_keluarga(payload: KeluargaCreateRequest):
    return service.gas_tambah_keluarga(payload)


@router.patch("/{keluarga_id}")
def patch_keluarga(keluarga_id: str, payload: KeluargaUpdateRequest):
    return service.gas_update_keluarga(keluarga_id, payload)


@router.delete("/{keluarga_id}")
def delete_keluarga(keluarga_id: str):
    return service.gas_hapus_keluarga(keluarga_id)


@router.patch("/{keluarga_id}/verifikasi")
def verifikasi_keluarga(keluarga_id: str, payload: KeluargaVerifikasiRequest):
    return service.gas_verifikasi_keluarga(keluarga_id, payload)