# app/modules/import_data/repository.py

import json
from uuid import uuid4
from typing import Any, Dict, List, Optional

from app.db.connection import ambil_koneksi


def bikin_uuid() -> str:
    """
    Membuat UUID dalam bentuk string.
    Dipakai supaya kolom id tidak null walaupun database belum punya default UUID.
    """
    return str(uuid4())


def bikin_import_batch(
    nama_file: str,
    jumlah_baris: int,
    uploaded_by: Optional[str] = None,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        import_batch_id = bikin_uuid()

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
                import_batch_id,
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
            raw_id = bikin_uuid()
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
                    raw_id,
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


def bersihkan_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    if text.lower() in ["nan", "none", "null", "-"]:
        return None

    return text


def normalisasi_jumlah_anggota(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        text = str(value).strip()

        if text == "":
            return None

        # Handle angka dari Excel seperti "5.0"
        number = int(float(text))

        if number <= 0:
            return None

        return number

    except Exception:
        return None


def upsert_keluarga_import(data: Dict[str, Any]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        keluarga_id = bikin_uuid()

        nama_kepala_keluarga = bersihkan_text(data.get("nama_kepala_keluarga"))
        nik = bersihkan_text(data.get("nik"))
        alamat = bersihkan_text(data.get("alamat"))
        kelurahan = bersihkan_text(data.get("kelurahan"))
        dusun = bersihkan_text(data.get("dusun"))
        jumlah_anggota = normalisasi_jumlah_anggota(data.get("jumlah_anggota"))

        if not nik:
            raise ValueError("NIK wajib ada saat mapping ke data keluarga.")

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
                keluarga_id,
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


def hapus_raw_by_batch(import_batch_id: str):
    """
    Optional helper.
    Dipakai kalau nanti kamu mau reset data raw berdasarkan batch tertentu.
    """
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM import_keluarga_raw
            WHERE import_batch_id = %s
            RETURNING id
            """,
            (import_batch_id,),
        )

        rows = cur.fetchall()
        conn.commit()

        return rows

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def hapus_import_batch(import_batch_id: str):
    """
    Optional helper.
    Menghapus batch import beserta raw data-nya.
    """
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM import_keluarga_raw
            WHERE import_batch_id = %s
            """,
            (import_batch_id,),
        )

        cur.execute(
            """
            DELETE FROM import_batch
            WHERE id = %s
            RETURNING
                id,
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by,
                created_at
            """,
            (import_batch_id,),
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