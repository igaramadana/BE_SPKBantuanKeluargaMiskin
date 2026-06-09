from fastapi import HTTPException

from app.modules.keluarga import repository
from app.modules.keluarga.schemas import (
    KeluargaCreateRequest,
    KeluargaUpdateRequest,
    KeluargaVerifikasiRequest,
)
from app.modules.user_account.service import ensure_user_account_for_verified_keluarga

VALID_STATUS = {"pending", "terverifikasi", "ditolak", "perlu_perbaikan"}


def gas_ambil_semua_keluarga(
    search: str | None = None,
    status_verifikasi: str | None = None,
    kelurahan: str | None = None,
    dusun: str | None = None,
):
    return repository.ambil_semua_keluarga(
        search=search,
        status_verifikasi=status_verifikasi,
        kelurahan=kelurahan,
        dusun=dusun,
    )


def gas_ambil_keluarga_detail(keluarga_id: str):
    keluarga = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    keluarga["penilaian"] = repository.ambil_penilaian_by_keluarga(keluarga_id)
    return keluarga


def gas_tambah_keluarga(payload: KeluargaCreateRequest):
    try:
        keluarga = repository.tambah_keluarga(payload.model_dump(exclude={"penilaian"}))

        penilaian_payload = payload.penilaian or []
        penilaian = repository.simpan_banyak_penilaian_manual(
            keluarga_id=keluarga["id"],
            penilaian=[item.model_dump() for item in penilaian_payload],
        )

        return {
            "message": "Data keluarga berhasil ditambahkan.",
            "data": keluarga,
            "penilaian": penilaian,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_update_keluarga(keluarga_id: str, payload: KeluargaUpdateRequest):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    try:
        data_update = payload.model_dump(
            exclude_unset=True,
            exclude={"penilaian"},
        )

        keluarga = repository.update_keluarga(keluarga_id, data_update)

        penilaian_payload = payload.penilaian or []
        penilaian = repository.simpan_banyak_penilaian_manual(
            keluarga_id=keluarga_id,
            penilaian=[item.model_dump() for item in penilaian_payload],
        )

        akun_user = None
        if data_update.get("status_verifikasi") == "terverifikasi":
            akun_user = ensure_user_account_for_verified_keluarga(keluarga_id)
            keluarga = repository.ambil_keluarga_by_id(keluarga_id)

        return {
            "message": "Data keluarga berhasil diperbarui.",
            "data": keluarga,
            "penilaian": penilaian,
            "akun_user": akun_user,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_hapus_keluarga(keluarga_id: str):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    try:
        keluarga = repository.hapus_keluarga(keluarga_id)
        return {
            "message": "Data keluarga berhasil dihapus.",
            "data": keluarga,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_verifikasi_keluarga(keluarga_id: str, payload: KeluargaVerifikasiRequest):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    if payload.status_verifikasi not in VALID_STATUS:
        raise HTTPException(
            status_code=400,
            detail="Status verifikasi tidak valid.",
        )

    try:
        keluarga = repository.verifikasi_keluarga(
            keluarga_id=keluarga_id,
            status_verifikasi=payload.status_verifikasi,
            catatan_admin=payload.catatan_admin,
        )

        akun_user = None

        if payload.status_verifikasi == "terverifikasi":
            akun_user = ensure_user_account_for_verified_keluarga(keluarga_id)
            keluarga = repository.ambil_keluarga_by_id(keluarga_id)

        return {
            "message": "Status keluarga berhasil diperbarui.",
            "data": keluarga,
            "akun_user": akun_user,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
