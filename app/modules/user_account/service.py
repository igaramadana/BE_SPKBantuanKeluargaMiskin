from uuid import uuid4
import bcrypt

from app.db.connection import ambil_koneksi


def _normalize_row(row):
    return dict(row) if row else None


def _hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def ensure_user_account_for_verified_keluarga(keluarga_id: str):
    """
    Membuat akun user otomatis untuk keluarga yang sudah terverifikasi.

    Login warga:
    - identifier: NIK
    - password awal: NIK
    """

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
                status_verifikasi
            FROM keluarga
            WHERE id = %s
            """,
            (keluarga_id,),
        )

        keluarga = _normalize_row(cur.fetchone())

        if not keluarga:
            raise ValueError("Data keluarga tidak ditemukan.")

        if keluarga["status_verifikasi"] != "terverifikasi":
            return {
                "created": False,
                "linked": False,
                "message": "Akun user tidak dibuat karena data keluarga belum terverifikasi.",
                "login": None,
            }

        if not keluarga.get("nik"):
            raise ValueError("NIK keluarga kosong, akun user tidak dapat dibuat.")

        if keluarga.get("user_id"):
            cur.execute(
                """
                SELECT id, nama, email, role
                FROM users
                WHERE id = %s
                """,
                (keluarga["user_id"],),
            )

            existing_user = _normalize_row(cur.fetchone())

            return {
                "created": False,
                "linked": True,
                "message": "Akun user sudah terhubung sebelumnya.",
                "user": existing_user,
                "login": {
                    "identifier": keluarga["nik"],
                    "password_awal": None,
                },
            }

        nik = str(keluarga["nik"]).strip()
        nama = keluarga.get("nama_kepala_keluarga") or f"Warga {nik}"
        email = f"{nik}@warga.local"
        password_hash = _hash_password(nik)
        user_id = str(uuid4())

        # Cek apakah user dengan email dummy sudah ada.
        cur.execute(
            """
            SELECT id, nama, email, role
            FROM users
            WHERE email = %s
            """,
            (email,),
        )

        existing_user = _normalize_row(cur.fetchone())

        if existing_user:
            user_id = existing_user["id"]
        else:
            cur.execute(
                """
                INSERT INTO users (
                    id,
                    nama,
                    email,
                    password_hash,
                    role,
                    must_change_password,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, 'user', TRUE, NOW(), NOW())
                RETURNING id, nama, email, role, must_change_password
                """,
                (
                    user_id,
                    nama,
                    email,
                    password_hash,
                ),
            )

            existing_user = _normalize_row(cur.fetchone())

        cur.execute(
            """
            UPDATE keluarga
            SET
                user_id = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, nama_kepala_keluarga, nik, status_verifikasi, user_id
            """,
            (
                user_id,
                keluarga_id,
            ),
        )

        updated_keluarga = _normalize_row(cur.fetchone())

        conn.commit()

        return {
            "created": True,
            "linked": True,
            "message": "Akun user berhasil dibuat dan dihubungkan ke data keluarga.",
            "user": existing_user,
            "keluarga": updated_keluarga,
            "login": {
                "identifier": nik,
                "password_awal": nik,
            },
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()