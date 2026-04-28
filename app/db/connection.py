import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

def ambil_koneksi():
    return psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor
    )