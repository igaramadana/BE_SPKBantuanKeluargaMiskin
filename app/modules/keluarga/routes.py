from fastapi import APIRouter, Query
from typing import Optional

from app.modules.keluarga.schemas import (
    KeluargaCreate,
    KeluargaUpdate,
    KeluargaVerifikasi,
)
from app.modules.keluarga import service

router = APIRouter()


@router.get("")
def ambil_semua_keluarga(
    search: Optional[str] = Query(default=None),
    kelurahan: Optional[str] = Query(default=None),
    dusun: Optional[str] = Query(default=None),
    status_verifikasi: Optional[str] = Query(default=None),
):
    return service.gas_ambil_semua_keluarga(
        search=search,
        kelurahan=kelurahan,
        dusun=dusun,
        status_verifikasi=status_verifikasi,
    )


@router.get("/{keluarga_id}")
def ambil_detail_keluarga(keluarga_id: str):
    return service.gas_ambil_detail_keluarga(keluarga_id)


@router.post("")
def tambah_keluarga(payload: KeluargaCreate):
    return service.gas_bikin_keluarga(payload)


@router.put("/{keluarga_id}")
def ubah_keluarga(keluarga_id: str, payload: KeluargaUpdate):
    return service.gas_update_keluarga(keluarga_id, payload)


@router.delete("/{keluarga_id}")
def hapus_keluarga(keluarga_id: str):
    return service.gas_hapus_keluarga(keluarga_id)


@router.patch("/{keluarga_id}/verifikasi")
def verifikasi_keluarga(keluarga_id: str, payload: KeluargaVerifikasi):
    return service.gas_verifikasi_keluarga(keluarga_id, payload)