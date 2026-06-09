from typing import Optional
from fastapi import APIRouter, Query
from app.db.connection import ambil_koneksi

router = APIRouter()


def normalize_rows(rows):
    return [dict(row) for row in rows]


@router.get("")
def get_audit_log(
    search: Optional[str] = Query(default=None),
    aksi: Optional[str] = Query(default=None),
    tabel: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        conditions = []
        values = []

        if search:
            conditions.append("""
                (
                    LOWER(COALESCE(aksi, '')) LIKE LOWER(%s)
                    OR LOWER(COALESCE(tabel, '')) LIKE LOWER(%s)
                    OR LOWER(COALESCE(record_id, '')) LIKE LOWER(%s)
                )
            """)
            values.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if aksi:
            conditions.append("aksi = %s")
            values.append(aksi)

        if tabel:
            conditions.append("tabel = %s")
            values.append(tabel)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        values.append(limit)

        cur.execute(f"""
            SELECT
                a.id,
                a.user_id,
                u.nama AS nama_user,
                a.aksi,
                a.tabel,
                a.record_id,
                a.before_json,
                a.after_json,
                a.created_at
            FROM audit_log a
            LEFT JOIN users u ON u.id = a.user_id
            {where_sql}
            ORDER BY a.created_at DESC
            LIMIT %s
        """, tuple(values))

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()
