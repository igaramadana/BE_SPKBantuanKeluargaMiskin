from fastapi import HTTPException

from app.modules.kriteria import repository


def gas_ambil_semua_kriteria():
    return repository.ambil_semua_kriteria()


def gas_ambil_kriteria_detail(kriteria_id: str):
    kriteria = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    return kriteria


def gas_tambah_kriteria(payload):
    try:
        existing = repository.ambil_kriteria_by_kode(payload.kode)

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Kode kriteria sudah digunakan.",
            )

        return repository.bikin_kriteria(payload)

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_update_kriteria(kriteria_id: str, payload):
    kriteria_lama = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria_lama:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    try:
        data_update = payload.model_dump(exclude_unset=True)

        return repository.update_kriteria(kriteria_id, data_update)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_hapus_kriteria(kriteria_id: str):
    kriteria_lama = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria_lama:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    try:
        return repository.nonaktifkan_kriteria(kriteria_id)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )