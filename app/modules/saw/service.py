from fastapi import HTTPException

from app.modules.saw import repository


def gas_simpan_penilaian(payload):
    try:
        return repository.simpan_penilaian(payload)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_hitung_dari_database(payload):
    try:
        data = payload.model_dump()

        return repository.hitung_saw_dari_database(data)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_ambil_hasil_terbaru():
    try:
        return repository.ambil_hasil_terbaru()

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_ambil_riwayat():
    try:
        return repository.ambil_riwayat()

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_auto_generate_penilaian_dari_import(import_batch_id: str | None):
    """
    Compatibility endpoint.

    Sekarang flow utama:
    Import Dataset -> Proses Dataset -> otomatis isi penilaian C1-C6.
    Jadi endpoint ini tidak wajib dipakai lagi.
    """
    return {
        "message": "Auto generate penilaian sekarang dilakukan dari menu Import Dataset.",
        "total_diproses": 0,
        "total_berhasil": 0,
        "total_gagal": 0,
        "errors": [
            "Gunakan menu Import Dataset -> Proses Dataset untuk otomatis membuat Data Warga + Penilaian C1-C6."
        ],
    }


# Alias supaya route lama tetap aman kalau masih ada yang memanggil nama lama.
def gas_simpan_penilaian_saw(payload):
    return gas_simpan_penilaian(payload)


def gas_hitung_saw_dari_database(payload):
    return gas_hitung_dari_database(payload)


def gas_ambil_hasil_saw_terbaru():
    return gas_ambil_hasil_terbaru()


def gas_ambil_riwayat_saw():
    return gas_ambil_riwayat()