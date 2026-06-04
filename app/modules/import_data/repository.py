import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.db.connection import ambil_koneksi


def bikin_uuid() -> str:
    return str(uuid4())


def bersihkan_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    if text.lower() in ["nan", "none", "null", "-"]:
        return None

    return text


def normalisasi_int(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        text = str(value).strip().replace(",", ".")

        if text == "":
            return None

        number = int(float(text))

        if number <= 0:
            return None

        return number

    except Exception:
        return None


def normalisasi_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        text = str(value).strip().replace(",", ".")

        if text == "":
            return None

        number = float(text)

        if number < 0:
            return None

        return number

    except Exception:
        return None


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
                created_at
            )
            VALUES (%s, %s, %s, 0, 0, %s, NOW())
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

        row = cur.fetchone()
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
    kolom_wajib: List[str],
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        jumlah_valid = 0
        jumlah_error = 0
        hasil = []

        for row in rows:
            errors = []

            for kolom in kolom_wajib:
                value = row.get(kolom)

                if value is None or str(value).strip() == "":
                    errors.append(f"Kolom {kolom} wajib diisi.")

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
                RETURNING
                    id,
                    import_batch_id,
                    raw_json,
                    status_validasi,
                    error_message,
                    created_at
                """,
                (
                    bikin_uuid(),
                    import_batch_id,
                    json.dumps(row, default=str),
                    status_validasi,
                    error_message,
                ),
            )

            hasil.append(cur.fetchone())

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
            "rows": hasil,
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


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

        return cur.fetchall()

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

        return cur.fetchone()

    finally:
        cur.close()
        conn.close()


def ambil_raw_by_batch(import_batch_id: str, only_valid: bool = False):
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

        return cur.fetchall()

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
            """
        )

        rows = cur.fetchall()

        return {str(row["kode"]).upper(): row for row in rows}

    finally:
        cur.close()
        conn.close()


def upsert_keluarga_import(data: Dict[str, Any]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        nama_kepala_keluarga = bersihkan_text(data.get("nama_kepala_keluarga"))
        nik = bersihkan_text(data.get("nik"))
        alamat = bersihkan_text(data.get("alamat"))
        kelurahan = bersihkan_text(data.get("kelurahan"))
        dusun = bersihkan_text(data.get("dusun"))
        jumlah_anggota = normalisasi_int(data.get("jumlah_anggota"))

        if not nik:
            raise ValueError("NIK wajib ada saat import data keluarga.")

        if not nama_kepala_keluarga:
            nama_kepala_keluarga = f"Keluarga Import {nik}"

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
                NULL,
                NULL,
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
                updated_at = NOW()
            RETURNING
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
                created_at,
                updated_at
            """,
            (
                bikin_uuid(),
                nama_kepala_keluarga,
                nik,
                alamat,
                kelurahan,
                dusun,
                jumlah_anggota,
            ),
        )

        row = cur.fetchone()
        conn.commit()
        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def simpan_penilaian_import(
    keluarga_id: str,
    kriteria_id: str,
    nilai_awal: float,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
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
            RETURNING
                id,
                keluarga_id,
                kriteria_id,
                sub_kriteria_id,
                nilai_awal,
                nilai_normalisasi,
                nilai_terbobot,
                created_at,
                updated_at
            """,
            (
                bikin_uuid(),
                keluarga_id,
                kriteria_id,
                nilai_awal,
            ),
        )

        row = cur.fetchone()
        conn.commit()
        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def proses_import_keluarga_dan_penilaian(
    import_batch_id: str,
    kolom_mapping: Dict[str, Optional[str]],
):
    raw_rows = ambil_raw_by_batch(import_batch_id, only_valid=True)
    kriteria_by_kode = ambil_kriteria_aktif_by_kode()

    skor_columns = {
        "C1": kolom_mapping.get("kolom_skor_c1") or "skor_C1_kondisi_rumah",
        "C2": kolom_mapping.get("kolom_skor_c2") or "skor_C2_jumlah_tanggungan",
        "C3": kolom_mapping.get("kolom_skor_c3")
        or "skor_C3_pekerjaan_kepala_keluarga",
        "C4": kolom_mapping.get("kolom_skor_c4")
        or "skor_C4_kepemilikan_aset_cost",
        "C5": kolom_mapping.get("kolom_skor_c5") or "skor_C5_fasilitas_dasar",
        "C6": kolom_mapping.get("kolom_skor_c6")
        or "skor_C6_pendidikan_kepala_keluarga",
    }

    total_diproses = 0
    total_berhasil = 0
    total_gagal = 0
    total_penilaian_berhasil = 0
    total_penilaian_gagal = 0
    errors = []

    for raw in raw_rows:
        total_diproses += 1

        try:
            raw_json = raw["raw_json"]

            if isinstance(raw_json, str):
                row_data: Dict[str, Any] = json.loads(raw_json)
            else:
                row_data = raw_json

            nama_col = kolom_mapping.get("kolom_nama_kepala_keluarga")
            nik_col = kolom_mapping.get("kolom_nik")
            alamat_col = kolom_mapping.get("kolom_alamat")
            kelurahan_col = kolom_mapping.get("kolom_kelurahan")
            dusun_col = kolom_mapping.get("kolom_dusun")
            anggota_col = kolom_mapping.get("kolom_jumlah_anggota")

            data_keluarga = {
                "nama_kepala_keluarga": row_data.get(nama_col) if nama_col else None,
                "nik": row_data.get(nik_col) if nik_col else None,
                "alamat": row_data.get(alamat_col) if alamat_col else None,
                "kelurahan": row_data.get(kelurahan_col) if kelurahan_col else None,
                "dusun": row_data.get(dusun_col) if dusun_col else None,
                "jumlah_anggota": row_data.get(anggota_col) if anggota_col else None,
            }

            keluarga = upsert_keluarga_import(data_keluarga)
            keluarga_id = keluarga["id"]

            for kode_kriteria, kolom_skor in skor_columns.items():
                kriteria = kriteria_by_kode.get(kode_kriteria)

                if not kriteria:
                    total_penilaian_gagal += 1
                    continue

                nilai = normalisasi_float(row_data.get(kolom_skor))

                if nilai is None:
                    total_penilaian_gagal += 1
                    continue

                simpan_penilaian_import(
                    keluarga_id=keluarga_id,
                    kriteria_id=kriteria["id"],
                    nilai_awal=nilai,
                )

                total_penilaian_berhasil += 1

            total_berhasil += 1

        except Exception as error:
            total_gagal += 1
            errors.append(str(error))

    return {
        "total_diproses": total_diproses,
        "total_berhasil": total_berhasil,
        "total_gagal": total_gagal,
        "total_penilaian_berhasil": total_penilaian_berhasil,
        "total_penilaian_gagal": total_penilaian_gagal,
        "errors": errors[:20],
    }