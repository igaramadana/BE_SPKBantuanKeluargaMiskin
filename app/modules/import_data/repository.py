from __future__ import annotations

import io
import json
import math
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pandas as pd

from app.db.connection import ambil_koneksi


REQUIRED_COLUMNS = ["kelurahan", "dusun", "jml_anggota_keluarga"]


def bikin_uuid() -> str:
    return str(uuid4())

def sanitize_json_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    if isinstance(value, Decimal):
        return float(value)

    return value


def sanitize_json_data(data):
    if isinstance(data, dict):
        return {
            str(key): sanitize_json_data(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [sanitize_json_data(item) for item in data]

    return sanitize_json_value(data)


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    if text.lower() in ["nan", "none", "null", "-", "tidak ada data"]:
        return None

    return text


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, float) and math.isnan(value):
        return None

    try:
        text = str(value).strip().replace(",", ".")

        if text == "":
            return None

        return float(text)

    except Exception:
        return None


def to_int(value: Any) -> Optional[int]:
    parsed = to_float(value)

    if parsed is None:
        return None

    return int(parsed)


def normalize_row(row):
    if row is None:
        return None

    result = {}

    for key, value in dict(row).items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value

    return result


def normalize_rows(rows):
    return [normalize_row(row) for row in rows]


async def baca_file_dataframe(file) -> pd.DataFrame:
    filename = file.filename or "dataset"
    content = await file.read()

    if filename.lower().endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(content))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin1")
    elif filename.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("Format file harus CSV, XLS, atau XLSX.")

    df.columns = [str(col).strip() for col in df.columns]

    # Bersihkan nilai NaN, inf, -inf agar aman untuk JSON.
    df = df.replace([float("inf"), float("-inf")], None)
    df = df.astype(object).where(pd.notnull(df), None)

    return df
    filename = file.filename or "dataset"
    content = await file.read()

    if filename.lower().endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(content))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding="latin1")
    elif filename.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("Format file harus CSV, XLS, atau XLSX.")

    df.columns = [str(col).strip() for col in df.columns]

    df = df.where(pd.notnull(df), None)

    return df


async def preview_import(file):
    df = await baca_file_dataframe(file)

    columns = list(df.columns)
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]

    preview_rows = df.head(10).to_dict(orient="records")
    preview_rows = sanitize_json_data(preview_rows)

    return {
        "filename": file.filename,
        "columns": columns,
        "total_rows": int(len(df)),
        "preview": preview_rows,
        "missing_required_columns": missing,
    }
    df = await baca_file_dataframe(file)
    columns = list(df.columns)
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]

    return {
        "filename": file.filename,
        "columns": columns,
        "total_rows": len(df),
        "preview": df.head(10).to_dict(orient="records"),
        "missing_required_columns": missing,
    }


def bikin_import_batch(
    nama_file: str,
    jumlah_baris: int,
    uploaded_by: Optional[str] = None,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO import_batch (
                id,
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by,
                status_proses,
                created_at
            )
            VALUES (%s, %s, %s, 0, 0, %s, 'raw', NOW())
            RETURNING
                id,
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by,
                created_at
            """,
            (
                bikin_uuid(),
                nama_file,
                jumlah_baris,
                uploaded_by,
            ),
        )

        row = normalize_row(cur.fetchone())
        conn.commit()

        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def simpan_raw_rows(
    import_batch_id: str,
    rows: List[Dict[str, Any]],
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        jumlah_valid = 0
        jumlah_error = 0

        for row in rows:
            errors = []

            for column in REQUIRED_COLUMNS:
                if clean_text(row.get(column)) is None:
                    errors.append(f"Kolom {column} wajib diisi.")

            status_validasi = "valid" if not errors else "error"
            error_message = "; ".join(errors) if errors else None

            if status_validasi == "valid":
                jumlah_valid += 1
            else:
                jumlah_error += 1

            cur.execute(
                """
                INSERT INTO import_keluarga_raw (
                    id,
                    import_batch_id,
                    raw_json,
                    status_validasi,
                    error_message,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    bikin_uuid(),
                    import_batch_id,
                    json.dumps(row, default=str),
                    status_validasi,
                    error_message,
                ),
            )

        cur.execute(
            """
            UPDATE import_batch
            SET
                jumlah_valid = %s,
                jumlah_error = %s
            WHERE id = %s
            """,
            (
                jumlah_valid,
                jumlah_error,
                import_batch_id,
            ),
        )

        conn.commit()

        return {
            "jumlah_valid": jumlah_valid,
            "jumlah_error": jumlah_error,
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


async def simpan_raw_import(file):
    df = await baca_file_dataframe(file)

    batch = bikin_import_batch(
        nama_file=file.filename or "dataset",
        jumlah_baris=int(len(df)),
        uploaded_by=None,
    )

    rows = df.to_dict(orient="records")
    rows = sanitize_json_data(rows)

    result = simpan_raw_rows(
        import_batch_id=batch["id"],
        rows=rows,
    )

    batch["jumlah_valid"] = result["jumlah_valid"]
    batch["jumlah_error"] = result["jumlah_error"]

    return {
        "message": "Dataset berhasil disimpan sebagai raw import.",
        "batch": sanitize_json_data(batch),
        "jumlah_valid": int(result["jumlah_valid"]),
        "jumlah_error": int(result["jumlah_error"]),
    }
    df = await baca_file_dataframe(file)

    batch = bikin_import_batch(
        nama_file=file.filename or "dataset",
        jumlah_baris=len(df),
        uploaded_by=None,
    )

    result = simpan_raw_rows(
        import_batch_id=batch["id"],
        rows=df.to_dict(orient="records"),
    )

    batch["jumlah_valid"] = result["jumlah_valid"]
    batch["jumlah_error"] = result["jumlah_error"]

    return {
        "message": "Dataset berhasil disimpan sebagai raw import.",
        "batch": batch,
        "jumlah_valid": result["jumlah_valid"],
        "jumlah_error": result["jumlah_error"],
    }


def ambil_import_batch():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by,
                created_at
            FROM import_batch
            ORDER BY created_at DESC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


def ambil_import_batch_by_id(import_batch_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by,
                created_at
            FROM import_batch
            WHERE id = %s
            """,
            (import_batch_id,),
        )

        return normalize_row(cur.fetchone())

    finally:
        cur.close()
        conn.close()


def ambil_raw_by_batch(import_batch_id: str, only_valid: bool = True):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        if only_valid:
            cur.execute(
                """
                SELECT
                    id,
                    import_batch_id,
                    raw_json,
                    status_validasi,
                    error_message,
                    created_at
                FROM import_keluarga_raw
                WHERE import_batch_id = %s
                  AND status_validasi = 'valid'
                ORDER BY created_at ASC
                """,
                (import_batch_id,),
            )
        else:
            cur.execute(
                """
                SELECT
                    id,
                    import_batch_id,
                    raw_json,
                    status_validasi,
                    error_message,
                    created_at
                FROM import_keluarga_raw
                WHERE import_batch_id = %s
                ORDER BY created_at ASC
                """,
                (import_batch_id,),
            )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


def ambil_kriteria_aktif_by_kode():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                kode,
                nama,
                jenis,
                bobot_ahp,
                aktif,
                urutan
            FROM kriteria
            WHERE aktif = true
            ORDER BY urutan ASC NULLS LAST, kode ASC
            """
        )

        rows = normalize_rows(cur.fetchall())

        return {str(row["kode"]).upper(): row for row in rows}

    finally:
        cur.close()
        conn.close()


def parse_raw_json(raw_json: Any) -> Dict[str, Any]:
    if isinstance(raw_json, str):
        return json.loads(raw_json)

    return raw_json


def build_group_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        clean_text(row.get("kelurahan")),
        clean_text(row.get("dusun")),
        clean_text(row.get("nama_sls")),
        to_int(row.get("jml_anggota_keluarga")),
        to_float(row.get("luas_lantai")),
        clean_text(row.get("lantai")),
        clean_text(row.get("dinding")),
        clean_text(row.get("kondisi_dinding")),
        clean_text(row.get("atap")),
        clean_text(row.get("kondisi_atap")),
        clean_text(row.get("sumber_air_minum")),
        clean_text(row.get("sumber_penerangan")),
        clean_text(row.get("daya")),
        clean_text(row.get("fas_bab")),
        clean_text(row.get("kloset")),
    )


def group_raw_rows(raw_rows: List[Dict[str, Any]]):
    grouped: Dict[Tuple[Any, ...], Dict[str, Any]] = {}

    for raw in raw_rows:
        row = parse_raw_json(raw["raw_json"])
        key = build_group_key(row)

        if key not in grouped:
            grouped[key] = row
            grouped[key]["_jumlah_baris_group"] = 1
        else:
            grouped[key]["_jumlah_baris_group"] += 1

    return list(grouped.values())


def nilai_ya_tidak(value: Any) -> int:
    text = (clean_text(value) or "").lower()

    if text in ["1", "ya", "y", "true", "ada", "punya", "memiliki"]:
        return 1

    return 0


def score_jumlah_anggota(value: Any) -> float:
    jumlah = to_int(value) or 1

    if jumlah >= 6:
        return 5
    if jumlah >= 4:
        return 4
    if jumlah == 3:
        return 3
    if jumlah == 2:
        return 2

    return 1


def score_luas_lantai(value: Any) -> float:
    luas = to_float(value)

    if luas is None or luas <= 0:
        return 5

    return luas


def score_lantai(value: Any) -> float:
    text = (clean_text(value) or "").lower()

    if "tanah" in text:
        return 5
    if "bambu" in text:
        return 4
    if "semen" in text or "plester" in text:
        return 3
    if "kayu" in text:
        return 3
    if "keramik" in text:
        return 2
    if "marmer" in text or "granit" in text:
        return 1

    return 3


def score_kondisi(value: Any) -> float:
    text = (clean_text(value) or "").lower()

    if "rusak berat" in text or "buruk" in text or "jelek" in text:
        return 5
    if "rusak sedang" in text:
        return 4
    if "rusak ringan" in text:
        return 3
    if "baik" in text:
        return 1

    return 3


def score_sumber_air(value: Any) -> float:
    text = (clean_text(value) or "").lower()

    if "sungai" in text or "hujan" in text or "danau" in text:
        return 5
    if "sumur" in text:
        return 4
    if "mata air" in text:
        return 3
    if "ledeng" in text or "pdam" in text:
        return 2
    if "kemasan" in text or "isi ulang" in text:
        return 1

    return 3


def score_daya_listrik(value: Any, sumber_penerangan: Any = None) -> float:
    sumber = (clean_text(sumber_penerangan) or "").lower()

    if "bukan listrik" in sumber or "tidak" in sumber:
        return 5

    daya = to_float(value)

    if daya is None or daya <= 0:
        return 5
    if daya <= 450:
        return 4
    if daya <= 900:
        return 3
    if daya <= 1300:
        return 2

    return 1


def score_fasilitas_bab(fas_bab: Any, kloset: Any) -> float:
    fas = (clean_text(fas_bab) or "").lower()
    klo = (clean_text(kloset) or "").lower()

    if "tidak" in fas or "tidak ada" in klo:
        return 5
    if "bersama" in fas or "umum" in fas:
        return 4
    if "sendiri" in fas:
        return 1

    return 3


def score_kendaraan(row: Dict[str, Any]) -> float:
    sepeda = nilai_ya_tidak(row.get("ada_sepeda"))
    motor = nilai_ya_tidak(row.get("ada_motor"))
    mobil = nilai_ya_tidak(row.get("ada_mobil"))

    if mobil:
        return 1
    if motor:
        return 2
    if sepeda:
        return 3

    return 5


def score_aset(row: Dict[str, Any]) -> float:
    aset_columns = [
        "ada_lemari_es",
        "ada_ac",
        "ada_tv",
        "ada_emas",
        "ada_laptop",
        "aset_tak_bergerak",
        "rumah_lain",
    ]

    jumlah_aset = sum(nilai_ya_tidak(row.get(col)) for col in aset_columns)

    jumlah_ternak = 0
    for col in [
        "jumlah_sapi",
        "jumlah_kerbau",
        "jumlah_kuda",
        "jumlah_babi",
        "jumlah_kambing",
    ]:
        jumlah_ternak += to_int(row.get(col)) or 0

    if jumlah_aset >= 4 or jumlah_ternak >= 5:
        return 1
    if jumlah_aset >= 2 or jumlah_ternak >= 2:
        return 2
    if jumlah_aset == 1 or jumlah_ternak == 1:
        return 3

    return 5


def generate_scores(row: Dict[str, Any]) -> Dict[str, float]:
    return {
        "C1": score_jumlah_anggota(row.get("jml_anggota_keluarga")),
        "C2": score_luas_lantai(row.get("luas_lantai")),
        "C3": score_lantai(row.get("lantai")),
        "C4": score_kondisi(row.get("kondisi_dinding") or row.get("dinding")),
        "C5": score_kondisi(row.get("kondisi_atap") or row.get("atap")),
        "C6": score_sumber_air(row.get("sumber_air_minum")),
        "C7": score_daya_listrik(row.get("daya"), row.get("sumber_penerangan")),
        "C8": score_fasilitas_bab(row.get("fas_bab"), row.get("kloset")),
        "C9": score_kendaraan(row),
        "C10": score_aset(row),
    }


def bikin_kode_keluarga_import(import_batch_id: str, index: int) -> str:
    short_batch = str(import_batch_id).split("-")[0].upper()

    return f"AUTO-MLATI-{short_batch}-{index:06d}"


def build_keluarga_data(row: Dict[str, Any], import_batch_id: str, index: int):
    kode_import = bikin_kode_keluarga_import(import_batch_id, index)

    kelurahan = clean_text(row.get("kelurahan"))
    dusun = clean_text(row.get("dusun"))
    nama_sls = clean_text(row.get("nama_sls"))

    alamat_parts = [part for part in [nama_sls, dusun, kelurahan] if part]
    alamat = ", ".join(alamat_parts) if alamat_parts else None

    return {
        "kode_keluarga_import": kode_import,
        "nama_kepala_keluarga": f"Keluarga {kode_import}",
        "nik": kode_import,
        "alamat": alamat,
        "kelurahan": kelurahan,
        "dusun": dusun,
        "jumlah_anggota": to_int(row.get("jml_anggota_keluarga")),
        "sumber_data": "import",
        "import_batch_id": import_batch_id,
    }


def upsert_keluarga_import(conn, data: Dict[str, Any]):
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO keluarga (
            id,
            user_id,
            nama_kepala_keluarga,
            nik,
            alamat,
            kelurahan,
            dusun,
            jumlah_anggota,
            status_verifikasi,
            catatan_admin,
            created_by,
            kode_keluarga_import,
            sumber_data,
            import_batch_id,
            created_at,
            updated_at
        )
        VALUES (
            %s,
            NULL,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'pending',
            'Data hasil import, perlu verifikasi admin.',
            NULL,
            %s,
            %s,
            %s,
            NOW(),
            NOW()
        )
        ON CONFLICT (nik)
        DO UPDATE SET
            nama_kepala_keluarga = EXCLUDED.nama_kepala_keluarga,
            alamat = EXCLUDED.alamat,
            kelurahan = EXCLUDED.kelurahan,
            dusun = EXCLUDED.dusun,
            jumlah_anggota = EXCLUDED.jumlah_anggota,
            kode_keluarga_import = EXCLUDED.kode_keluarga_import,
            sumber_data = EXCLUDED.sumber_data,
            import_batch_id = EXCLUDED.import_batch_id,
            updated_at = NOW()
        RETURNING
            id,
            nama_kepala_keluarga,
            nik,
            alamat,
            kelurahan,
            dusun,
            jumlah_anggota,
            status_verifikasi,
            kode_keluarga_import,
            sumber_data,
            import_batch_id,
            created_at,
            updated_at
        """,
        (
            bikin_uuid(),
            data["nama_kepala_keluarga"],
            data["nik"],
            data["alamat"],
            data["kelurahan"],
            data["dusun"],
            data["jumlah_anggota"],
            data["kode_keluarga_import"],
            data["sumber_data"],
            data["import_batch_id"],
        ),
    )

    return normalize_row(cur.fetchone())


def simpan_penilaian_import(conn, keluarga_id: str, kriteria_id: str, nilai_awal: float):
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO penilaian (
            id,
            keluarga_id,
            kriteria_id,
            sub_kriteria_id,
            nilai_awal,
            nilai_normalisasi,
            nilai_terbobot,
            created_at,
            updated_at
        )
        VALUES (
            %s,
            %s,
            %s,
            NULL,
            %s,
            NULL,
            NULL,
            NOW(),
            NOW()
        )
        ON CONFLICT (keluarga_id, kriteria_id)
        DO UPDATE SET
            nilai_awal = EXCLUDED.nilai_awal,
            sub_kriteria_id = NULL,
            nilai_normalisasi = NULL,
            nilai_terbobot = NULL,
            updated_at = NOW()
        RETURNING id
        """,
        (
            bikin_uuid(),
            keluarga_id,
            kriteria_id,
            nilai_awal,
        ),
    )

    return normalize_row(cur.fetchone())


def auto_generate_penilaian_dari_dataset(
    import_batch_id: str,
    preview_only: bool = True,
    limit_preview: int = 50,
):
    raw_rows = ambil_raw_by_batch(import_batch_id, only_valid=True)

    if not raw_rows:
        raise ValueError("Raw import tidak ditemukan atau tidak ada data valid.")

    grouped_rows = group_raw_rows(raw_rows)
    kriteria_by_kode = ambil_kriteria_aktif_by_kode()

    required_kode = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]
    missing_kriteria = [kode for kode in required_kode if kode not in kriteria_by_kode]

    if missing_kriteria:
        raise ValueError(
            "Kriteria aktif belum lengkap. Kode yang belum ada: "
            + ", ".join(missing_kriteria)
        )

    preview = []
    errors = []
    total_gagal = 0
    total_keluarga_berhasil = 0
    total_penilaian_berhasil = 0

    conn = None

    try:
        if not preview_only:
            conn = ambil_koneksi()

        for index, row in enumerate(grouped_rows, start=1):
            try:
                keluarga_data = build_keluarga_data(row, import_batch_id, index)
                scores = generate_scores(row)

                preview_item = {
                    "kode_keluarga_import": keluarga_data["kode_keluarga_import"],
                    "nama_kepala_keluarga": keluarga_data["nama_kepala_keluarga"],
                    "nik": keluarga_data["nik"],
                    "kelurahan": keluarga_data["kelurahan"],
                    "dusun": keluarga_data["dusun"],
                    "jumlah_anggota": keluarga_data["jumlah_anggota"],
                    "jumlah_baris_group": row.get("_jumlah_baris_group", 1),
                    "scores": scores,
                    "raw_ringkas": {
                        "status": row.get("status"),
                        "nama_sls": row.get("nama_sls"),
                        "luas_lantai": row.get("luas_lantai"),
                        "lantai": row.get("lantai"),
                        "kondisi_dinding": row.get("kondisi_dinding"),
                        "kondisi_atap": row.get("kondisi_atap"),
                        "sumber_air_minum": row.get("sumber_air_minum"),
                        "daya": row.get("daya"),
                    },
                }

                if len(preview) < limit_preview:
                    preview.append(preview_item)

                if preview_only:
                    continue

                keluarga = upsert_keluarga_import(conn, keluarga_data)
                total_keluarga_berhasil += 1

                for kode, nilai in scores.items():
                    kriteria = kriteria_by_kode[kode]

                    simpan_penilaian_import(
                        conn=conn,
                        keluarga_id=keluarga["id"],
                        kriteria_id=kriteria["id"],
                        nilai_awal=nilai,
                    )

                    total_penilaian_berhasil += 1

            except Exception as error:
                total_gagal += 1

                if len(errors) < 30:
                    errors.append(f"Baris group {index}: {str(error)}")

        if not preview_only and conn is not None:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE import_batch
                SET status_proses = 'generated'
                WHERE id = %s
                """,
                (import_batch_id,),
            )
            conn.commit()

        return {
                "message": (
                    "Preview auto generate penilaian berhasil dibuat."
                    if preview_only
                    else "Auto generate keluarga dan penilaian berhasil disimpan."
                ),

                # Field baru
                "import_batch_id": import_batch_id,
                "preview_only": preview_only,
                "total_raw": int(len(raw_rows)),
                "total_grouped": int(len(grouped_rows)),
                "total_keluarga_berhasil": int(total_keluarga_berhasil),
                "total_penilaian_berhasil": int(total_penilaian_berhasil),
                "total_gagal": int(total_gagal),
                "preview": preview,
                "errors": errors,

                # Field lama / backward compatibility untuk frontend mapping lama
                "total_diproses": int(len(grouped_rows)),
                "total_berhasil": int(total_keluarga_berhasil),
                "total_penilaian_gagal": int(total_gagal),
                "total_penilaian_berhasil": int(total_penilaian_berhasil),
            }

    except Exception as error:
        if conn is not None:
            conn.rollback()

        raise error

    finally:
        if conn is not None:
            conn.close()