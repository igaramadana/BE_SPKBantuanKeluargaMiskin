from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from app.db.connection import ambil_koneksi

router = APIRouter()


@router.get("/hasil-ranking/pdf")
def export_hasil_ranking_pdf(riwayat_id: str | None = None):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        if not riwayat_id:
            cur.execute("""
                SELECT id
                FROM riwayat_perhitungan
                ORDER BY tanggal_hitung DESC
                LIMIT 1
            """)
            latest = cur.fetchone()

            if not latest:
                raise HTTPException(status_code=404, detail="Belum ada riwayat perhitungan.")

            riwayat_id = latest["id"]

        cur.execute("""
            SELECT
                r.nama_perhitungan,
                r.metode,
                r.mode_status,
                r.threshold,
                r.kuota,
                r.reserve_quota,
                r.tanggal_hitung
            FROM riwayat_perhitungan r
            WHERE r.id = %s
        """, (riwayat_id,))
        riwayat = cur.fetchone()

        if not riwayat:
            raise HTTPException(status_code=404, detail="Riwayat tidak ditemukan.")

        cur.execute("""
            SELECT
                h.ranking,
                k.nama_kepala_keluarga,
                k.nik,
                k.kelurahan,
                k.dusun,
                h.total_nilai,
                h.status_sistem,
                COALESCE(h.status_final, h.status_sistem) AS status_final
            FROM hasil_spk h
            JOIN keluarga k ON k.id = h.keluarga_id
            WHERE h.riwayat_perhitungan_id = %s
            ORDER BY h.ranking ASC
        """, (riwayat_id,))
        rows = cur.fetchall()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Laporan Hasil Ranking SPK Bantuan Keluarga Miskin", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Nama Perhitungan: {riwayat['nama_perhitungan']}", styles["Normal"]))
        elements.append(Paragraph(f"Metode: {riwayat['metode']}", styles["Normal"]))
        elements.append(Paragraph(f"Mode Status: {riwayat['mode_status']}", styles["Normal"]))
        elements.append(Paragraph(f"Tanggal Hitung: {riwayat['tanggal_hitung']}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        data = [[
            "Rank",
            "Nama Kepala Keluarga",
            "NIK",
            "Kelurahan",
            "Dusun",
            "Nilai",
            "Status Final",
        ]]

        for row in rows:
            data.append([
                row["ranking"],
                row["nama_kepala_keluarga"],
                row["nik"],
                row["kelurahan"] or "-",
                row["dusun"] or "-",
                f"{float(row['total_nilai']):.4f}",
                row["status_final"],
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=hasil-ranking-spk.pdf"},
        )

    finally:
        cur.close()
        conn.close()
