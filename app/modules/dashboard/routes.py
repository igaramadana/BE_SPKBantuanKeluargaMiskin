from fastapi import APIRouter
from app.db.connection import ambil_koneksi

router = APIRouter()


def normalize_row(row):
    return dict(row) if row else None


def normalize_rows(rows):
    return [dict(row) for row in rows]


@router.get("/statistik")
def get_dashboard_statistik():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                COUNT(*) AS total_keluarga,
                COUNT(*) FILTER (WHERE status_verifikasi = 'pending') AS total_pending,
                COUNT(*) FILTER (WHERE status_verifikasi = 'terverifikasi') AS total_terverifikasi,
                COUNT(*) FILTER (WHERE status_verifikasi = 'ditolak') AS total_ditolak,
                COUNT(*) FILTER (WHERE status_verifikasi = 'perlu_perbaikan') AS total_perlu_perbaikan
            FROM keluarga
        """)
        keluarga = normalize_row(cur.fetchone())

        cur.execute("""
            SELECT
                COUNT(*) AS total_hasil,
                COUNT(*) FILTER (WHERE COALESCE(status_final, status_sistem) = 'layak') AS total_layak,
                COUNT(*) FILTER (WHERE COALESCE(status_final, status_sistem) = 'cadangan') AS total_cadangan,
                COUNT(*) FILTER (WHERE COALESCE(status_final, status_sistem) = 'tidak_layak') AS total_tidak_layak
            FROM hasil_spk
            WHERE riwayat_perhitungan_id = (
                SELECT id FROM riwayat_perhitungan
                ORDER BY tanggal_hitung DESC
                LIMIT 1
            )
        """)
        hasil = normalize_row(cur.fetchone())

        cur.execute("""
            SELECT kelurahan, COUNT(*) AS total
            FROM keluarga
            WHERE kelurahan IS NOT NULL
            GROUP BY kelurahan
            ORDER BY total DESC
            LIMIT 10
        """)
        per_kelurahan = normalize_rows(cur.fetchall())

        cur.execute("""
            SELECT id, nama_perhitungan, metode, jumlah_data, mode_status, threshold, kuota, reserve_quota, tanggal_hitung
            FROM riwayat_perhitungan
            ORDER BY tanggal_hitung DESC
            LIMIT 1
        """)
        riwayat_terakhir = normalize_row(cur.fetchone())

        return {
            "keluarga": keluarga,
            "hasil": hasil,
            "per_kelurahan": per_kelurahan,
            "riwayat_terakhir": riwayat_terakhir,
        }

    finally:
        cur.close()
        conn.close()
