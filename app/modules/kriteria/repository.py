from app.db.connection import ambil_koneksi


def ambil_semua_kriteria():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, kode, nama, jenis, bobot_ahp, aktif, urutan, created_at, updated_at
        FROM kriteria
        ORDER BY urutan ASC NULLS LAST, kode ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def bikin_kriteria(data):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO kriteria (kode, nama, jenis, aktif, urutan)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, kode, nama, jenis, bobot_ahp, aktif, urutan, created_at, updated_at
            """,
            (
                data.kode,
                data.nama,
                data.jenis,
                data.aktif,
                data.urutan,
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