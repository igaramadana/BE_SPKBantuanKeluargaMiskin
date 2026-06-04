import io
import math
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.modules.import_data import repository
from app.modules.import_data.schemas import MappingImportRequest


DEFAULT_REQUIRED_COLUMNS = [
    "kelurahan",
    "dusun",
    "jml_anggota_keluarga",
]


def sanitize_json_value(value: Any):
    """
    Membersihkan value agar aman dikirim sebagai JSON.
    Masalah utama pandas: NaN / Infinity tidak valid untuk JSON response FastAPI.
    """
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        text = value.strip()

        if text.lower() in ["nan", "none", "null", ""]:
            return None

        return value

    if isinstance(value, dict):
        return {str(k): sanitize_json_value(v) for k, v in value.items()}

    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]

    if pd.isna(value):
        return None

    return value


def sanitize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {str(key): sanitize_json_value(value) for key, value in row.items()}
        for row in records
    ]


def normalisasi_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [str(col).strip() for col in df.columns]

    # Ganti NaN, NaT, inf, -inf menjadi None agar aman untuk JSON dan insert raw.
    df = df.replace([float("inf"), float("-inf")], None)
    df = df.where(pd.notnull(df), None)

    return df


async def baca_file_dataset(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    content = await file.read()

    try:
        if filename.lower().endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(content))
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding="latin1")

        elif filename.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))

        else:
            raise HTTPException(
                status_code=400,
                detail="Format file tidak didukung. Gunakan CSV, XLS, atau XLSX.",
            )

        return normalisasi_dataframe(df)

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Gagal membaca file dataset: {str(error)}",
        )


def cek_missing_columns(columns: List[str], required_columns: List[str]):
    normalized_columns = {str(col).strip() for col in columns}

    return [column for column in required_columns if column not in normalized_columns]


async def gas_preview_dataset(file: UploadFile):
    df = await baca_file_dataset(file)

    columns = [str(col) for col in df.columns]
    missing = cek_missing_columns(columns, DEFAULT_REQUIRED_COLUMNS)

    preview_records = df.head(8).to_dict(orient="records")
    preview = sanitize_records(preview_records)

    return {
        "filename": file.filename,
        "columns": columns,
        "total_rows": int(len(df)),
        "preview": preview,
        "missing_required_columns": missing,
    }


async def gas_simpan_raw_dataset(
    file: UploadFile,
    uploaded_by: Optional[str] = None,
):
    df = await baca_file_dataset(file)

    columns = [str(col) for col in df.columns]
    missing = cek_missing_columns(columns, DEFAULT_REQUIRED_COLUMNS)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Kolom wajib tidak ditemukan: {', '.join(missing)}",
        )

    raw_rows: List[Dict[str, Any]] = df.to_dict(orient="records")
    rows = sanitize_records(raw_rows)

    try:
        batch = repository.bikin_import_batch(
            nama_file=file.filename or "dataset",
            jumlah_baris=len(rows),
            uploaded_by=uploaded_by,
        )

        hasil_raw = repository.simpan_raw_rows(
            import_batch_id=batch["id"],
            rows=rows,
            kolom_wajib=DEFAULT_REQUIRED_COLUMNS,
        )

        updated_batch = repository.ambil_import_batch_by_id(batch["id"])

        return {
            "message": "Raw dataset berhasil disimpan.",
            "batch": sanitize_json_value(updated_batch),
            "jumlah_valid": hasil_raw["jumlah_valid"],
            "jumlah_error": hasil_raw["jumlah_error"],
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_ambil_import_batch():
    try:
        rows = repository.ambil_import_batch()
        return sanitize_json_value(rows)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_ambil_import_batches():
    return gas_ambil_import_batch()


def gas_proses_import_keluarga_dan_penilaian(payload: MappingImportRequest):
    batch = repository.ambil_import_batch_by_id(payload.import_batch_id)

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch import tidak ditemukan.",
        )

    kolom_mapping = {
        "kolom_nama_kepala_keluarga": payload.kolom_nama_kepala_keluarga,
        "kolom_nik": payload.kolom_nik,
        "kolom_alamat": payload.kolom_alamat,
        "kolom_kelurahan": payload.kolom_kelurahan,
        "kolom_dusun": payload.kolom_dusun,
        "kolom_jumlah_anggota": payload.kolom_jumlah_anggota,
        "kolom_skor_c1": payload.kolom_skor_c1,
        "kolom_skor_c2": payload.kolom_skor_c2,
        "kolom_skor_c3": payload.kolom_skor_c3,
        "kolom_skor_c4": payload.kolom_skor_c4,
        "kolom_skor_c5": payload.kolom_skor_c5,
        "kolom_skor_c6": payload.kolom_skor_c6,
    }

    try:
        hasil = repository.proses_import_keluarga_dan_penilaian(
            import_batch_id=payload.import_batch_id,
            kolom_mapping=kolom_mapping,
        )

        return sanitize_json_value(
            {
                "message": "Dataset berhasil diproses ke Data Warga dan Penilaian.",
                "total_diproses": hasil["total_diproses"],
                "total_berhasil": hasil["total_berhasil"],
                "total_gagal": hasil["total_gagal"],
                "total_penilaian_berhasil": hasil["total_penilaian_berhasil"],
                "total_penilaian_gagal": hasil["total_penilaian_gagal"],
                "errors": hasil.get("errors", []),
            }
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


def gas_ambil_detail_batch(import_batch_id: str):
    batch = repository.ambil_import_batch_by_id(import_batch_id)

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch import tidak ditemukan.",
        )

    rows = repository.ambil_raw_by_batch(import_batch_id, only_valid=False)

    return sanitize_json_value(
        {
            "batch": batch,
            "rows": rows,
        }
    )