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


def ambil_semua_keluarga(
    search: Optional[str] = None,
    status_verifikasi: Optional[str] = None,
    kelurahan: Optional[str] = None,
    dusun: Optional[str] = None,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        conditions = []
        values = []

        if search:
            conditions.append(
                "(LOWER(nama_kepala_keluarga) LIKE LOWER(%s) OR LOWER(nik) LIKE LOWER(%s))"
            )
            values.extend([f"%{search}%", f"%{search}%"])

        if status_verifikasi:
            conditions.append("status_verifikasi = %s")
            values.append(status_verifikasi)

        if kelurahan:
            conditions.append("kelurahan = %s")
            values.append(kelurahan)

        if dusun:
            conditions.append("dusun = %s")
            values.append(dusun)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cur.execute(
            f"""
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
            {where_sql}
            ORDER BY created_at DESC
            """,
            tuple(values),
        )

        return cur.fetchall()

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

        return cur.fetchone()

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


def ambil_penilaian_by_keluarga(keluarga_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                p.id,
                p.keluarga_id,
                p.kriteria_id,
                k.kode AS kode_kriteria,
                k.nama AS nama_kriteria,
                p.sub_kriteria_id,
                p.nilai_awal,
                p.nilai_normalisasi,
                p.nilai_terbobot,
                p.created_at,
                p.updated_at
            FROM penilaian p
            JOIN kriteria k ON k.id = p.kriteria_id
            WHERE p.keluarga_id = %s
            ORDER BY k.urutan ASC NULLS LAST, k.kode ASC
            """,
            (keluarga_id,),
        )

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def tambah_keluarga(data: Dict[str, Any]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        keluarga_id = bikin_uuid()

        nama_kepala_keluarga = bersihkan_text(data.get("nama_kepala_keluarga"))
        nik = bersihkan_text(data.get("nik"))
        alamat = bersihkan_text(data.get("alamat"))
        kelurahan = bersihkan_text(data.get("kelurahan"))
        dusun = bersihkan_text(data.get("dusun"))
        jumlah_anggota = normalisasi_int(data.get("jumlah_anggota"))

        if not nama_kepala_keluarga:
            raise ValueError("Nama kepala keluarga wajib diisi.")

        if not nik:
            raise ValueError("NIK wajib diisi.")

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


def update_keluarga(keluarga_id: str, data: Dict[str, Any]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    allowed_fields = {
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

    for key, value in data.items():
        if key not in allowed_fields:
            continue

        if key == "jumlah_anggota":
            value = normalisasi_int(value)

        if key in [
            "nama_kepala_keluarga",
            "nik",
            "alamat",
            "kelurahan",
            "dusun",
            "catatan_admin",
        ]:
            value = bersihkan_text(value)

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
    catatan_admin: Optional[str] = None,
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


def simpan_penilaian_manual(
    keluarga_id: str,
    kode_kriteria: str,
    nilai_awal: float,
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        kode = str(kode_kriteria).upper().strip()
        nilai = normalisasi_float(nilai_awal)

        if nilai is None:
            raise ValueError(f"Nilai {kode} tidak valid.")

        cur.execute(
            """
            SELECT id
            FROM kriteria
            WHERE kode = %s
              AND aktif = true
            """,
            (kode,),
        )

        kriteria = cur.fetchone()

        if not kriteria:
            raise ValueError(f"Kriteria aktif dengan kode {kode} tidak ditemukan.")

        penilaian_id = bikin_uuid()

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
                penilaian_id,
                keluarga_id,
                kriteria["id"],
                nilai,
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


def simpan_banyak_penilaian_manual(
    keluarga_id: str,
    penilaian: List[Dict[str, Any]],
):
    hasil = []

    for item in penilaian:
        kode_kriteria = item.get("kode_kriteria")
        nilai_awal = item.get("nilai_awal")

        if kode_kriteria is None or nilai_awal is None:
            continue

        row = simpan_penilaian_manual(
            keluarga_id=keluarga_id,
            kode_kriteria=kode_kriteria,
            nilai_awal=nilai_awal,
        )

        hasil.append(row)

    return hasil