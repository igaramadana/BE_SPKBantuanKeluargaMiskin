from fastapi import APIRouter, HTTPException, Query
from app.db.connection import ambil_koneksi

router = APIRouter()


def normalize_row(row):
    return dict(row) if row else None


def mask_nik(nik: str | None) -> str | None:
    if not nik:
        return None

    nik = str(nik)

    if len(nik) <= 6:
        return nik[0:2] + "*" * max(len(nik) - 2, 0)

    return nik[:6] + "*" * max(len(nik) - 8, 0) + nik[-2:]


def mask_name(name: str | None) -> str | None:
    if not name:
        return None

    name = str(name).strip()
    parts = name.split()

    if len(parts) == 1:
        if len(name) <= 2:
            return name[0] + "*"
        return name[:2] + "*" * max(len(name) - 2, 3)

    first = parts[0]
    second_initial = parts[1][0] + "******" if len(parts) > 1 else ""

    return f"{first} {second_initial}".strip()


def format_status_label(status: str | None) -> str:
    if not status:
        return "Belum Diketahui"

    mapping = {
        "pending": "Menunggu Verifikasi",
        "terverifikasi": "Terverifikasi",
        "ditolak": "Ditolak",
        "perlu_perbaikan": "Perlu Perbaikan",
        "layak": "Layak",
        "cadangan": "Cadangan",
        "tidak_layak": "Tidak Layak",
        "belum_dihitung": "Belum Dihitung",
    }

    return mapping.get(status, status.replace("_", " ").title())


@router.get("/cek-kelayakan")
def cek_kelayakan(nik: str = Query(..., min_length=16, max_length=16)):
    """
    Endpoint public untuk cek status bantuan berdasarkan NIK.

    Data yang dikembalikan sengaja dibatasi:
    - nama dimasking
    - NIK dimasking
    - status verifikasi
    - status bantuan final
    - ranking jika sudah ada hasil SPK

    Data sensitif seperti alamat, penghasilan, detail nilai, dan catatan admin
    tidak ditampilkan di endpoint public.
    """

    clean_nik = "".join(filter(str.isdigit, nik))

    if len(clean_nik) != 16:
        raise HTTPException(
            status_code=400,
            detail="NIK harus berisi 16 digit angka.",
        )

    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        # 1. Cari data keluarga berdasarkan NIK
        cur.execute(
            """
            SELECT
                id,
                nama_kepala_keluarga,
                nik,
                status_verifikasi
            FROM keluarga
            WHERE nik = %s
            LIMIT 1
            """,
            (clean_nik,),
        )

        keluarga = normalize_row(cur.fetchone())

        if not keluarga:
            return {
                "found": False,
                "status": "not_found",
                "nama": None,
                "nik_masked": mask_nik(clean_nik),
                "status_verifikasi": None,
                "status_verifikasi_label": None,
                "status_bantuan": None,
                "status_bantuan_label": None,
                "ranking": None,
                "tanggal_hitung": None,
                "message": "Data dengan NIK tersebut tidak ditemukan.",
            }

        status_verifikasi = keluarga.get("status_verifikasi")

        # 2. Kalau belum terverifikasi, jangan cek hasil SPK dulu
        if status_verifikasi != "terverifikasi":
            message_map = {
                "pending": "Data Anda sudah terdaftar dan masih menunggu proses verifikasi admin.",
                "perlu_perbaikan": "Data Anda perlu diperbaiki. Silakan login atau hubungi admin untuk informasi lebih lanjut.",
                "ditolak": "Data Anda ditolak berdasarkan proses verifikasi admin.",
            }

            return {
                "found": True,
                "status": status_verifikasi,
                "nama": mask_name(keluarga.get("nama_kepala_keluarga")),
                "nik_masked": mask_nik(keluarga.get("nik")),
                "status_verifikasi": status_verifikasi,
                "status_verifikasi_label": format_status_label(status_verifikasi),
                "status_bantuan": "belum_dihitung",
                "status_bantuan_label": "Belum Dihitung",
                "ranking": None,
                "tanggal_hitung": None,
                "message": message_map.get(
                    status_verifikasi,
                    "Data Anda belum dapat diproses ke tahap perhitungan bantuan.",
                ),
            }

        # 3. Jika sudah terverifikasi, ambil hasil SPK terbaru milik keluarga
        cur.execute(
            """
            SELECT
                h.id,
                h.total_nilai,
                h.ranking,
                h.status_sistem,
                h.status_final,
                h.tanggal_hitung,
                r.nama_perhitungan,
                r.metode,
                r.tanggal_hitung AS tanggal_riwayat
            FROM hasil_spk h
            LEFT JOIN riwayat_perhitungan r
                ON r.id = h.riwayat_perhitungan_id
            WHERE h.keluarga_id = %s
            ORDER BY
                COALESCE(r.tanggal_hitung, h.tanggal_hitung) DESC,
                h.tanggal_hitung DESC
            LIMIT 1
            """,
            (keluarga["id"],),
        )

        hasil = normalize_row(cur.fetchone())

        # 4. Sudah terverifikasi, tapi belum pernah masuk hasil SAW/SPK
        if not hasil:
            return {
                "found": True,
                "status": "belum_dihitung",
                "nama": mask_name(keluarga.get("nama_kepala_keluarga")),
                "nik_masked": mask_nik(keluarga.get("nik")),
                "status_verifikasi": status_verifikasi,
                "status_verifikasi_label": "Terverifikasi",
                "status_bantuan": "belum_dihitung",
                "status_bantuan_label": "Belum Dihitung",
                "ranking": None,
                "tanggal_hitung": None,
                "message": "Data Anda sudah terverifikasi dan menunggu proses perhitungan bantuan.",
            }

        # 5. Prioritaskan status_final jika ada override admin
        status_bantuan = hasil.get("status_final") or hasil.get("status_sistem")

        message_by_status = {
            "layak": "Data Anda masuk daftar layak penerima bantuan.",
            "cadangan": "Data Anda masuk daftar cadangan penerima bantuan.",
            "tidak_layak": "Data Anda belum masuk daftar penerima bantuan.",
        }

        tanggal_hitung = hasil.get("tanggal_riwayat") or hasil.get("tanggal_hitung")

        return {
            "found": True,
            "status": status_bantuan,
            "nama": mask_name(keluarga.get("nama_kepala_keluarga")),
            "nik_masked": mask_nik(keluarga.get("nik")),
            "status_verifikasi": status_verifikasi,
            "status_verifikasi_label": "Terverifikasi",
            "status_bantuan": status_bantuan,
            "status_bantuan_label": format_status_label(status_bantuan),
            "ranking": hasil.get("ranking"),
            "tanggal_hitung": tanggal_hitung,
            "message": message_by_status.get(
                status_bantuan,
                "Status bantuan Anda sudah tersedia.",
            ),
        }

    finally:
        cur.close()
        conn.close()