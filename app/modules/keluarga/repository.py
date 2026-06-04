from typing import Optional
from uuid import uuid4

from app.db.connection import ambil_koneksi


def bikin_uuid() -> str:
    return str(uuid4())


def ambil_semua_keluarga(
    search: Optional[str] = None,
    kelurahan: Optional[str] = None,
    dusun: Optional[str] = None,
    status_verifikasi: Optional[str] = None,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    conditions = []
    values = []

    if search:
        conditions.append("(nama_kepala_keluarga ILIKE %s OR nik ILIKE %s)")
        values.append(f"%{search}%")
        values.append(f"%{search}%")

    if kelurahan:
        conditions.append("kelurahan = %s")
        values.append(kelurahan)

    if dusun:
        conditions.append("dusun = %s")
        values.append(dusun)

    if status_verifikasi:
        conditions.append("status_verifikasi = %s")
        values.append(status_verifikasi)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
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
        FROM keluarga
        {where_clause}
        ORDER BY created_at DESC
    """

    try:
        cur.execute(query, tuple(values))
        rows = cur.fetchall()
        return rows

    finally:
        cur.close()
        conn.close()


def ambil_keluarga_by_id(keluarga_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
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
            FROM keluarga
            WHERE id = %s
            """,
            (keluarga_id,),
        )

        row = cur.fetchone()
        return row

    finally:
        cur.close()
        conn.close()


def ambil_keluarga_by_nik(nik: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
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
            FROM keluarga
            WHERE nik = %s
            """,
            (nik,),
        )

        row = cur.fetchone()
        return row

    finally:
        cur.close()
        conn.close()


def bikin_keluarga(data):
    conn = ambil_koneksi()
    cur = conn.cursor()

    keluarga_id = bikin_uuid()

    try:
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
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'pending',
                NULL,
                %s,
                NOW(),
                NOW()
            )
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
                data.user_id,
                data.nama_kepala_keluarga,
                data.nik,
                data.alamat,
                data.kelurahan,
                data.dusun,
                data.jumlah_anggota,
                data.created_by,
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


def update_keluarga(keluarga_id: str, data_dict: dict):
    conn = ambil_koneksi()
    cur = conn.cursor()

    allowed_fields = {
        "user_id",
        "nama_kepala_keluarga",
        "nik",
        "alamat",
        "kelurahan",
        "dusun",
        "jumlah_anggota",
        "status_verifikasi",
        "catatan_admin",
    }

    fields = []
    values = []

    for key, value in data_dict.items():
        if key not in allowed_fields:
            continue

        fields.append(f"{key} = %s")
        values.append(value)

    if not fields:
        cur.close()
        conn.close()
        return ambil_keluarga_by_id(keluarga_id)

    values.append(keluarga_id)

    query = f"""
        UPDATE keluarga
        SET {", ".join(fields)}, updated_at = NOW()
        WHERE id = %s
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
    """

    try:
        cur.execute(query, tuple(values))
        row = cur.fetchone()
        conn.commit()
        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def hapus_keluarga(keluarga_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM keluarga
            WHERE id = %s
            RETURNING id
            """,
            (keluarga_id,),
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


def verifikasi_keluarga(
    keluarga_id: str,
    status_verifikasi: str,
    catatan_admin: Optional[str],
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE keluarga
            SET
                status_verifikasi = %s,
                catatan_admin = %s,
                updated_at = NOW()
            WHERE id = %s
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
                status_verifikasi,
                catatan_admin,
                keluarga_id,
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