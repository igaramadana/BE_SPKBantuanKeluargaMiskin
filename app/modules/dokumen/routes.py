import os
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from app.db.connection import ambil_koneksi

router = APIRouter()

UPLOAD_DIR = "uploads/dokumen"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def normalize_row(row):
    return dict(row) if row else None


def normalize_rows(rows):
    return [dict(row) for row in rows]


@router.get("/keluarga/{keluarga_id}")
def get_dokumen_keluarga(keluarga_id: str):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id,
                keluarga_id,
                jenis_dokumen,
                file_url,
                status_verifikasi,
                catatan,
                reviewed_by,
                reviewed_at,
                created_at,
                updated_at
            FROM dokumen_keluarga
            WHERE keluarga_id = %s
            ORDER BY created_at DESC
        """, (keluarga_id,))
        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


@router.post("/upload")
async def upload_dokumen_keluarga(
    keluarga_id: str = Form(...),
    jenis_dokumen: str = Form(...),
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File tidak valid.")

    allowed_ext = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Format file harus PDF/JPG/PNG/WEBP.")

    saved_name = f"{uuid4()}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 5MB.")

    with open(saved_path, "wb") as f:
        f.write(content)

    file_url = f"/uploads/dokumen/{saved_name}"

    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        dokumen_id = str(uuid4())

        cur.execute("""
            INSERT INTO dokumen_keluarga (
                id,
                keluarga_id,
                jenis_dokumen,
                file_url,
                status_verifikasi,
                catatan,
                reviewed_by,
                reviewed_at,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, 'pending', NULL, NULL, NULL, NOW(), NOW())
            RETURNING
                id,
                keluarga_id,
                jenis_dokumen,
                file_url,
                status_verifikasi,
                catatan,
                reviewed_by,
                reviewed_at,
                created_at,
                updated_at
        """, (dokumen_id, keluarga_id, jenis_dokumen, file_url))

        row = normalize_row(cur.fetchone())
        conn.commit()
        return {
            "message": "Dokumen berhasil diupload.",
            "data": row,
        }

    except Exception as error:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        cur.close()
        conn.close()


@router.patch("/{dokumen_id}/verifikasi")
def verifikasi_dokumen(
    dokumen_id: str,
    status_verifikasi: str = Query(...),
    catatan: Optional[str] = Query(default=None),
    reviewed_by: Optional[str] = Query(default=None),
):
    allowed = ["pending", "diterima", "ditolak"]

    if status_verifikasi not in allowed:
        raise HTTPException(status_code=400, detail="Status dokumen tidak valid.")

    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE dokumen_keluarga
            SET
                status_verifikasi = %s,
                catatan = %s,
                reviewed_by = NULLIF(%s, '')::uuid,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING
                id,
                keluarga_id,
                jenis_dokumen,
                file_url,
                status_verifikasi,
                catatan,
                reviewed_by,
                reviewed_at,
                created_at,
                updated_at
        """, (status_verifikasi, catatan, reviewed_by or "", dokumen_id))

        row = normalize_row(cur.fetchone())

        if not row:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")

        conn.commit()

        return {
            "message": "Status dokumen berhasil diperbarui.",
            "data": row,
        }

    except Exception as error:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        cur.close()
        conn.close()
