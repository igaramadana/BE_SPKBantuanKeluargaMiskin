from app.db.connection import ambil_koneksi


def ambil_semua_kriteria():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            kode,
            nama,
            jenis,
            bobot_ahp,
            aktif,
            urutan,
            created_at,
            updated_at
        FROM kriteria
        ORDER BY urutan ASC NULLS LAST, kode ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_kriteria_by_id(kriteria_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            kode,
            nama,
            jenis,
            bobot_ahp,
            aktif,
            urutan,
            created_at,
            updated_at
        FROM kriteria
        WHERE id = %s
        """,
        (kriteria_id,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def ambil_kriteria_by_kode(kode: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            kode,
            nama,
            jenis,
            bobot_ahp,
            aktif,
            urutan,
            created_at,
            updated_at
        FROM kriteria
        WHERE kode = %s
        """,
        (kode,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def bikin_kriteria(data):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO kriteria (
                kode,
                nama,
                jenis,
                aktif,
                urutan
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING
                id,
                kode,
                nama,
                jenis,
                bobot_ahp,
                aktif,
                urutan,
                created_at,
                updated_at
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


def update_kriteria(kriteria_id: str, data_dict: dict):
    conn = ambil_koneksi()
    cur = conn.cursor()

    fields = []
    values = []

    for key, value in data_dict.items():
        fields.append(f"{key} = %s")
        values.append(value)

    values.append(kriteria_id)

    query = f"""
        UPDATE kriteria
        SET {", ".join(fields)}, updated_at = NOW()
        WHERE id = %s
        RETURNING
            id,
            kode,
            nama,
            jenis,
            bobot_ahp,
            aktif,
            urutan,
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


def nonaktifkan_kriteria(kriteria_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE kriteria
            SET aktif = false, updated_at = NOW()
            WHERE id = %s
            RETURNING
                id,
                kode,
                nama,
                jenis,
                bobot_ahp,
                aktif,
                urutan,
                created_at,
                updated_at
            """,
            (kriteria_id,),
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