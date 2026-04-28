from fastapi import HTTPException
from app.modules.keluarga import repository


STATUS_VERIFIKASI_VALID = [
    "pending",
    "terverifikasi",
    "ditolak",
    "perlu_perbaikan",
]


def gas_ambil_semua_keluarga(
    search=None,
    kelurahan=None,
    dusun=None,
    status_verifikasi=None,
):
    if status_verifikasi and status_verifikasi not in STATUS_VERIFIKASI_VALID:
        raise HTTPException(
            status_code=400,
            detail="Status verifikasi tidak valid.",
        )

    return repository.ambil_semua_keluarga(
        search=search,
        kelurahan=kelurahan,
        dusun=dusun,
        status_verifikasi=status_verifikasi,
    )


def gas_ambil_detail_keluarga(keluarga_id: str):
    keluarga = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    return keluarga


def gas_bikin_keluarga(payload):
    keluarga_lama = repository.ambil_keluarga_by_nik(payload.nik)

    if keluarga_lama:
        raise HTTPException(
            status_code=400,
            detail="NIK sudah terdaftar.",
        )

    try:
        return repository.bikin_keluarga(payload)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_update_keluarga(keluarga_id: str, payload):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    data_dict = payload.model_dump(exclude_unset=True)

    if not data_dict:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada data yang diubah.",
        )

    if "status_verifikasi" in data_dict:
        if data_dict["status_verifikasi"] not in STATUS_VERIFIKASI_VALID:
            raise HTTPException(
                status_code=400,
                detail="Status verifikasi tidak valid.",
            )

    if "nik" in data_dict and data_dict["nik"] != keluarga_lama["nik"]:
        nik_sudah_ada = repository.ambil_keluarga_by_nik(data_dict["nik"])

        if nik_sudah_ada:
            raise HTTPException(
                status_code=400,
                detail="NIK sudah digunakan data keluarga lain.",
            )

    try:
        return repository.update_keluarga(keluarga_id, data_dict)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_hapus_keluarga(keluarga_id: str):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    try:
        deleted = repository.hapus_keluarga(keluarga_id)

        return {
            "message": "Data keluarga berhasil dihapus.",
            "data": deleted,
        }

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_verifikasi_keluarga(keluarga_id: str, payload):
    keluarga_lama = repository.ambil_keluarga_by_id(keluarga_id)

    if not keluarga_lama:
        raise HTTPException(
            status_code=404,
            detail="Data keluarga tidak ditemukan.",
        )

    if payload.status_verifikasi not in STATUS_VERIFIKASI_VALID:
        raise HTTPException(
            status_code=400,
            detail="Status verifikasi tidak valid.",
        )

    try:
        return repository.verifikasi_keluarga(
            keluarga_id=keluarga_id,
            status_verifikasi=payload.status_verifikasi,
            catatan_admin=payload.catatan_admin,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))