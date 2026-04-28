from fastapi import HTTPException
import pandas as pd
from app.modules.import_data import repository


KOLOM_WAJIB_DEFAULT = [
    "kelurahan",
    "dusun",
    "jml_anggota_keluarga",
]


def baca_file_ke_dataframe(file):
    nama_file = file.filename or ""

    if not nama_file.endswith((".csv", ".xls", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="File harus berformat CSV, XLS, atau XLSX.",
        )

    try:
        if nama_file.endswith(".csv"):
            return pd.read_csv(file.file), nama_file

        return pd.read_excel(file.file), nama_file

    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(error)}")


def bersihin_dataframe(df):
    df = df.fillna("")
    df.columns = [str(column).strip() for column in df.columns]
    return df


def intip_file(file):
    df, nama_file = baca_file_ke_dataframe(file)
    df = bersihin_dataframe(df)

    daftar_kolom = list(df.columns)

    kolom_kurang = [
        kolom for kolom in KOLOM_WAJIB_DEFAULT
        if kolom not in daftar_kolom
    ]

    return {
        "filename": nama_file,
        "total_rows": len(df),
        "columns": daftar_kolom,
        "missing_required_columns": kolom_kurang,
        "preview": df.head(10).to_dict(orient="records"),
    }


def gas_simpan_raw_import(file, uploaded_by=None):
    df, nama_file = baca_file_ke_dataframe(file)
    df = bersihin_dataframe(df)

    rows = df.to_dict(orient="records")

    try:
        batch = repository.bikin_import_batch(
            nama_file=nama_file,
            jumlah_baris=len(df),
            uploaded_by=uploaded_by,
        )

        hasil_raw = repository.simpan_raw_rows(
            import_batch_id=batch["id"],
            rows=rows,
            kolom_wajib=KOLOM_WAJIB_DEFAULT,
        )

        return {
            "message": "Import raw berhasil disimpan.",
            "batch": {
                **batch,
                "jumlah_valid": hasil_raw["jumlah_valid"],
                "jumlah_error": hasil_raw["jumlah_error"],
            },
            "sample": hasil_raw["rows"][:10],
        }

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_ambil_semua_batch():
    return repository.ambil_import_batch()


def gas_ambil_detail_batch(import_batch_id: str):
    batch = repository.ambil_import_batch_by_id(import_batch_id)

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Import batch tidak ditemukan.",
        )

    rows = repository.ambil_raw_by_batch(import_batch_id)

    return {
        "batch": batch,
        "rows": rows,
    }


def gas_mapping_ke_keluarga(payload):
    batch = repository.ambil_import_batch_by_id(payload.import_batch_id)

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Import batch tidak ditemukan.",
        )

    rows = repository.ambil_raw_by_batch(payload.import_batch_id, only_valid=True)

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada data valid untuk dimapping.",
        )

    hasil = []
    gagal = []

    for item in rows:
        raw = item["raw_json"]

        try:
            nik = None

            if payload.kolom_nik and payload.kolom_nik in raw:
                nik = str(raw[payload.kolom_nik]).strip()

            if not nik:
                nik = f"IMPORT-{item['id']}"

            nama_kepala_keluarga = None

            if payload.kolom_nama_kepala_keluarga and payload.kolom_nama_kepala_keluarga in raw:
                nama_kepala_keluarga = str(raw[payload.kolom_nama_kepala_keluarga]).strip()

            if not nama_kepala_keluarga:
                nama_kepala_keluarga = f"Keluarga Import {item['id']}"

            data_keluarga = {
                "nama_kepala_keluarga": nama_kepala_keluarga,
                "nik": nik,
                "alamat": raw.get(payload.kolom_alamat) if payload.kolom_alamat else None,
                "kelurahan": raw.get(payload.kolom_kelurahan),
                "dusun": raw.get(payload.kolom_dusun),
                "jumlah_anggota": int(float(raw.get(payload.kolom_jumlah_anggota) or 0)),
            }

            keluarga = repository.upsert_keluarga_import(data_keluarga)
            hasil.append(keluarga)

        except Exception as error:
            gagal.append(
                {
                    "raw_id": item["id"],
                    "error": str(error),
                }
            )

    return {
        "message": "Mapping import ke keluarga selesai.",
        "total_diproses": len(rows),
        "total_berhasil": len(hasil),
        "total_gagal": len(gagal),
        "berhasil": hasil,
        "gagal": gagal,
    }