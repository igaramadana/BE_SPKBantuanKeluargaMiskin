from fastapi import HTTPException, UploadFile

from app.modules.import_data import repository


async def gas_preview_import(file: UploadFile):
    try:
        return await repository.preview_import(file)

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


async def gas_simpan_raw_import(file: UploadFile):
    try:
        return await repository.simpan_raw_import(file)

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_ambil_import_batch():
    try:
        return repository.ambil_import_batch()

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_ambil_import_batch_by_id(import_batch_id: str):
    try:
        row = repository.ambil_import_batch_by_id(import_batch_id)

        if not row:
            raise ValueError("Import batch tidak ditemukan.")

        return row

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_auto_generate_penilaian(payload):
    try:
        return repository.auto_generate_penilaian_dari_dataset(
            import_batch_id=payload.import_batch_id,
            preview_only=payload.preview_only,
            limit_preview=payload.limit_preview,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


# Endpoint lama tetap diarahkan ke auto generate baru.
def gas_proses_import_keluarga_dan_penilaian(payload):
    try:
        return repository.auto_generate_penilaian_dari_dataset(
            import_batch_id=payload.import_batch_id,
            preview_only=False,
            limit_preview=50,
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))