from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.db.connection import ambil_koneksi


def ambil_kriteria_aktif_dengan_bobot():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            kode,
            nama,
            jenis,
            bobot_ahp
        FROM kriteria
        WHERE aktif = true
        ORDER BY urutan ASC NULLS LAST, kode ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_keluarga_terverifikasi():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            nama_kepala_keluarga,
            nik,
            kelurahan,
            dusun
        FROM keluarga
        WHERE status_verifikasi = 'terverifikasi'
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_penilaian_aktif():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            p.id,
            p.keluarga_id,
            p.kriteria_id,
            p.sub_kriteria_id,
            p.nilai_awal,
            p.nilai_normalisasi,
            p.nilai_terbobot,
            k.kode AS kode_kriteria,
            k.nama AS nama_kriteria,
            k.jenis AS jenis_kriteria,
            k.bobot_ahp
        FROM penilaian p
        JOIN kriteria k ON k.id = p.kriteria_id
        WHERE k.aktif = true
        ORDER BY p.keluarga_id, k.urutan ASC NULLS LAST, k.kode ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def simpan_penilaian_batch(data: List[Dict[str, Any]]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        hasil = []

        for item in data:
            cur.execute(
                """
                INSERT INTO penilaian (
                    keluarga_id,
                    kriteria_id,
                    sub_kriteria_id,
                    nilai_awal
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (keluarga_id, kriteria_id)
                DO UPDATE SET
                    sub_kriteria_id = EXCLUDED.sub_kriteria_id,
                    nilai_awal = EXCLUDED.nilai_awal,
                    updated_at = NOW()
                RETURNING
                    id,
                    keluarga_id,
                    kriteria_id,
                    sub_kriteria_id,
                    nilai_awal,
                    nilai_normalisasi,
                    nilai_terbobot
                """,
                (
                    item["keluarga_id"],
                    item["kriteria_id"],
                    item.get("sub_kriteria_id"),
                    item["nilai_awal"],
                ),
            )

            hasil.append(cur.fetchone())

        conn.commit()
        return hasil

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def update_penilaian_hasil(keluarga_id: str, kode_kriteria: str, nilai_normalisasi: float, nilai_terbobot: float):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE penilaian p
            SET
                nilai_normalisasi = %s,
                nilai_terbobot = %s,
                updated_at = NOW()
            FROM kriteria k
            WHERE
                p.kriteria_id = k.id
                AND p.keluarga_id = %s
                AND k.kode = %s
            RETURNING p.id
            """,
            (
                nilai_normalisasi,
                nilai_terbobot,
                keluarga_id,
                kode_kriteria,
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


def bikin_riwayat_perhitungan(
    nama_perhitungan: str,
    jumlah_data: int,
    mode_status: str,
    threshold: Optional[float],
    kuota: Optional[int],
    dihitung_oleh: Optional[str],
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO riwayat_perhitungan (
                nama_perhitungan,
                metode,
                jumlah_data,
                mode_status,
                threshold,
                kuota,
                dihitung_oleh
            )
            VALUES (%s, 'AHP-SAW', %s, %s, %s, %s, %s)
            RETURNING id, nama_perhitungan, jumlah_data, mode_status, threshold, kuota, tanggal_hitung
            """,
            (
                nama_perhitungan,
                jumlah_data,
                mode_status,
                threshold,
                kuota,
                dihitung_oleh,
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


def hapus_hasil_by_riwayat(riwayat_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM hasil_spk
            WHERE riwayat_perhitungan_id = %s
            """,
            (riwayat_id,),
        )

        conn.commit()

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def simpan_hasil_spk_batch(riwayat_id: str, data: List[Dict[str, Any]]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        hasil = []

        for item in data:
            cur.execute(
                """
                INSERT INTO hasil_spk (
                    keluarga_id,
                    riwayat_perhitungan_id,
                    total_nilai,
                    ranking,
                    status_sistem,
                    status_final
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    keluarga_id,
                    riwayat_perhitungan_id,
                    total_nilai,
                    ranking,
                    status_sistem,
                    status_final,
                    tanggal_hitung
                """,
                (
                    item["keluarga_id"],
                    riwayat_id,
                    item["total_nilai"],
                    item["ranking"],
                    item["status"],
                    item["status"],
                ),
            )

            hasil.append(cur.fetchone())

        conn.commit()
        return hasil

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def ambil_hasil_spk_terbaru():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            h.id,
            h.keluarga_id,
            k.nama_kepala_keluarga,
            k.nik,
            k.kelurahan,
            k.dusun,
            h.total_nilai,
            h.ranking,
            h.status_sistem,
            h.status_final,
            h.tanggal_hitung,
            h.riwayat_perhitungan_id
        FROM hasil_spk h
        JOIN keluarga k ON k.id = h.keluarga_id
        WHERE h.riwayat_perhitungan_id = (
            SELECT id
            FROM riwayat_perhitungan
            ORDER BY tanggal_hitung DESC
            LIMIT 1
        )
        ORDER BY h.ranking ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_riwayat_perhitungan():
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            nama_perhitungan,
            metode,
            jumlah_data,
            consistency_ratio,
            mode_status,
            threshold,
            kuota,
            tanggal_hitung,
            dihitung_oleh
        FROM riwayat_perhitungan
        ORDER BY tanggal_hitung DESC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def ambil_hasil_by_riwayat(riwayat_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            h.id,
            h.keluarga_id,
            k.nama_kepala_keluarga,
            k.nik,
            k.kelurahan,
            k.dusun,
            h.total_nilai,
            h.ranking,
            h.status_sistem,
            h.status_final,
            h.tanggal_hitung,
            h.riwayat_perhitungan_id
        FROM hasil_spk h
        JOIN keluarga k ON k.id = h.keluarga_id
        WHERE h.riwayat_perhitungan_id = %s
        ORDER BY h.ranking ASC
        """,
        (riwayat_id,),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows