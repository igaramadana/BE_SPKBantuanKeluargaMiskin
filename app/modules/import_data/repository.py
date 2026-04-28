import json
from typing import List, Dict, Any
from app.db.connection import ambil_koneksi


def bikin_import_batch(nama_file: str, jumlah_baris: int, uploaded_by=None):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO import_batch (
                nama_file,
                jumlah_baris,
                jumlah_valid,
                jumlah_error,
                uploaded_by
            )
            VALUES (%s, %s, 0, 0, %s)
            RETURNING id, nama_file, jumlah_baris, jumlah_valid, jumlah_error, created_at
            """,
            (
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


def simpan_raw_rows(import_batch_id: str, rows: List[Dict[str, Any]], kolom_wajib: List[str]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        jumlah_valid = 0
        jumlah_error = 0
        hasil = []

        for row in rows:
            errors = []

            for kolom in kolom_wajib:
                if kolom not in row or row[kolom] in [None, ""]:
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
                    import_batch_id,
                    raw_json,
                    status_validasi,
                    error_message
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id, import_batch_id, raw_json, status_validasi, error_message, created_at
                """,
                (
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
            SET jumlah_valid = %s, jumlah_error = %s
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

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_import_batch_by_id(import_batch_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

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

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def ambil_raw_by_batch(import_batch_id: str, only_valid: bool = False):
    conn = ambil_koneksi()
    cur = conn.cursor()

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

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def upsert_keluarga_import(data: Dict[str, Any]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO keluarga (
                nama_kepala_keluarga,
                nik,
                alamat,
                kelurahan,
                dusun,
                jumlah_anggota,
                status_verifikasi
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
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
                nama_kepala_keluarga,
                nik,
                alamat,
                kelurahan,
                dusun,
                jumlah_anggota,
                status_verifikasi
            """,
            (
                data["nama_kepala_keluarga"],
                data["nik"],
                data.get("alamat"),
                data.get("kelurahan"),
                data.get("dusun"),
                data.get("jumlah_anggota"),
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