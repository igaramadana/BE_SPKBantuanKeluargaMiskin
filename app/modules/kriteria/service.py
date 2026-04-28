from fastapi import HTTPException
from app.modules.kriteria import repository


JENIS_KRITERIA_VALID = ["benefit", "cost"]


def gas_ambil_semua_kriteria():
    return repository.ambil_semua_kriteria()


def gas_ambil_detail_kriteria(kriteria_id: str):
    kriteria = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    return kriteria


def gas_bikin_kriteria(payload):
    if payload.jenis not in JENIS_KRITERIA_VALID:
        raise HTTPException(
            status_code=400,
            detail="Jenis kriteria harus benefit atau cost.",
        )

    kriteria_lama = repository.ambil_kriteria_by_kode(payload.kode)

    if kriteria_lama:
        raise HTTPException(
            status_code=400,
            detail="Kode kriteria sudah digunakan.",
        )

    try:
        return repository.bikin_kriteria(payload)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_update_kriteria(kriteria_id: str, payload):
    kriteria_lama = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria_lama:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    data_dict = payload.model_dump(exclude_unset=True)

    if not data_dict:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada data yang diubah.",
        )

    if "jenis" in data_dict and data_dict["jenis"] not in JENIS_KRITERIA_VALID:
        raise HTTPException(
            status_code=400,
            detail="Jenis kriteria harus benefit atau cost.",
        )

    if "kode" in data_dict and data_dict["kode"] != kriteria_lama["kode"]:
        kode_sudah_ada = repository.ambil_kriteria_by_kode(data_dict["kode"])

        if kode_sudah_ada:
            raise HTTPException(
                status_code=400,
                detail="Kode kriteria sudah digunakan.",
            )

    try:
        return repository.update_kriteria(kriteria_id, data_dict)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_hapus_kriteria(kriteria_id: str):
    kriteria_lama = repository.ambil_kriteria_by_id(kriteria_id)

    if not kriteria_lama:
        raise HTTPException(
            status_code=404,
            detail="Kriteria tidak ditemukan.",
        )

    try:
        hasil = repository.nonaktifkan_kriteria(kriteria_id)

        return {
            "message": "Kriteria berhasil dinonaktifkan.",
            "data": hasil,
        }

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))