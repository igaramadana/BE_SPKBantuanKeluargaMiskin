from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.db.connection import ambil_koneksi


def bikin_uuid() -> str:
    return str(uuid4())


def normalisasi_uuid(value: Any) -> Optional[str]:
    """
    Kolom dihitung_oleh di database kamu bertipe UUID.
    Kalau frontend kirim 'Administrator', nilainya akan dibuat NULL.
    """
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    try:
        UUID(text)
        return text
    except Exception:
        return None


def to_float(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, Decimal):
        return float(value)

    try:
        return float(value)
    except Exception:
        return 0.0


def safe_value(value: Any):
    if isinstance(value, Decimal):
        return float(value)

    return value


def normalize_row(row):
    if row is None:
        return None

    return {key: safe_value(value) for key, value in dict(row).items()}


def normalize_rows(rows):
    return [normalize_row(row) for row in rows]


def simpan_penilaian(payload):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        hasil = []

        for item in payload.data:
            penilaian_id = bikin_uuid()

            cur.execute(
                """
                INSERT INTO penilaian (
                    id,
                    keluarga_id,
                    kriteria_id,
                    sub_kriteria_id,
                    nilai_awal,
                    nilai_normalisasi,
                    nilai_terbobot,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    NULL,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (keluarga_id, kriteria_id)
                DO UPDATE SET
                    sub_kriteria_id = EXCLUDED.sub_kriteria_id,
                    nilai_awal = EXCLUDED.nilai_awal,
                    nilai_normalisasi = NULL,
                    nilai_terbobot = NULL,
                    updated_at = NOW()
                RETURNING
                    id,
                    keluarga_id,
                    kriteria_id,
                    sub_kriteria_id,
                    nilai_awal,
                    nilai_normalisasi,
                    nilai_terbobot,
                    created_at,
                    updated_at
                """,
                (
                    penilaian_id,
                    item.keluarga_id,
                    item.kriteria_id,
                    item.sub_kriteria_id,
                    item.nilai_awal,
                ),
            )

            hasil.append(normalize_row(cur.fetchone()))

        conn.commit()

        return {
            "message": "Penilaian berhasil disimpan.",
            "data": hasil,
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def ambil_kriteria_aktif():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                kode,
                nama,
                jenis,
                COALESCE(bobot_ahp, 0) AS bobot_ahp,
                aktif,
                urutan
            FROM kriteria
            WHERE aktif = true
            ORDER BY urutan ASC NULLS LAST, kode ASC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


def ambil_data_penilaian_terverifikasi():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                k.id AS keluarga_id,
                k.nama_kepala_keluarga,
                k.nik,
                k.kelurahan,
                k.dusun,
                kr.id AS kriteria_id,
                kr.kode AS kode_kriteria,
                kr.nama AS nama_kriteria,
                kr.jenis,
                COALESCE(kr.bobot_ahp, 0) AS bobot_ahp,
                p.nilai_awal
            FROM keluarga k
            JOIN penilaian p ON p.keluarga_id = k.id
            JOIN kriteria kr ON kr.id = p.kriteria_id
            WHERE k.status_verifikasi = 'terverifikasi'
              AND kr.aktif = true
            ORDER BY k.created_at ASC, kr.urutan ASC NULLS LAST, kr.kode ASC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


def bentuk_matrix_penilaian(rows: List[Dict[str, Any]], kriteria: List[Dict[str, Any]]):
    keluarga_map: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        keluarga_id = row["keluarga_id"]
        kriteria_id = row["kriteria_id"]

        if keluarga_id not in keluarga_map:
            keluarga_map[keluarga_id] = {
                "keluarga_id": keluarga_id,
                "nama_kepala_keluarga": row["nama_kepala_keluarga"],
                "nik": row["nik"],
                "kelurahan": row.get("kelurahan"),
                "dusun": row.get("dusun"),
                "nilai": {},
            }

        keluarga_map[keluarga_id]["nilai"][kriteria_id] = to_float(row["nilai_awal"])

    lengkap = []
    tidak_lengkap = []

    required_kriteria_ids = [item["id"] for item in kriteria]

    for keluarga in keluarga_map.values():
        missing = [
            kriteria_id
            for kriteria_id in required_kriteria_ids
            if kriteria_id not in keluarga["nilai"]
        ]

        if missing:
            tidak_lengkap.append(
                {
                    "keluarga_id": keluarga["keluarga_id"],
                    "nama_kepala_keluarga": keluarga["nama_kepala_keluarga"],
                    "missing_kriteria": missing,
                }
            )
        else:
            lengkap.append(keluarga)

    return lengkap, tidak_lengkap


def normalisasi_saw(keluarga_rows: List[Dict[str, Any]], kriteria: List[Dict[str, Any]]):
    pembagi = {}

    for item_kriteria in kriteria:
        kriteria_id = item_kriteria["id"]
        jenis = item_kriteria["jenis"]

        values = [
            to_float(keluarga["nilai"].get(kriteria_id))
            for keluarga in keluarga_rows
        ]

        if not values:
            pembagi[kriteria_id] = 0
            continue

        if jenis == "benefit":
            pembagi[kriteria_id] = max(values)
        else:
            positive_values = [value for value in values if value > 0]
            pembagi[kriteria_id] = min(positive_values) if positive_values else 0

    hasil = []

    for keluarga in keluarga_rows:
        total_nilai = 0.0
        detail_nilai = []

        for item_kriteria in kriteria:
            kriteria_id = item_kriteria["id"]
            jenis = item_kriteria["jenis"]
            bobot = to_float(item_kriteria["bobot_ahp"])
            nilai_awal = to_float(keluarga["nilai"].get(kriteria_id))
            divisor = to_float(pembagi.get(kriteria_id))

            if divisor <= 0 or nilai_awal <= 0:
                nilai_normalisasi = 0.0
            elif jenis == "benefit":
                nilai_normalisasi = nilai_awal / divisor
            else:
                nilai_normalisasi = divisor / nilai_awal

            nilai_terbobot = nilai_normalisasi * bobot
            total_nilai += nilai_terbobot

            detail_nilai.append(
                {
                    "kriteria_id": kriteria_id,
                    "kode": item_kriteria["kode"],
                    "nilai_awal": nilai_awal,
                    "nilai_normalisasi": nilai_normalisasi,
                    "nilai_terbobot": nilai_terbobot,
                }
            )

        hasil.append(
            {
                "keluarga_id": keluarga["keluarga_id"],
                "nama_kepala_keluarga": keluarga["nama_kepala_keluarga"],
                "nik": keluarga["nik"],
                "kelurahan": keluarga.get("kelurahan"),
                "dusun": keluarga.get("dusun"),
                "total_nilai": total_nilai,
                "detail": detail_nilai,
            }
        )

    hasil.sort(key=lambda item: item["total_nilai"], reverse=True)

    for index, item in enumerate(hasil, start=1):
        item["ranking"] = index

    return hasil


def tentukan_status(hasil: List[Dict[str, Any]], mode: str, threshold, quota, reserve_quota):
    parsed_threshold = to_float(threshold)
    parsed_quota = int(quota or 0)
    parsed_reserve = int(reserve_quota or 0)

    for item in hasil:
        if mode == "threshold":
            item["status_sistem"] = (
                "layak" if item["total_nilai"] >= parsed_threshold else "tidak_layak"
            )
        else:
            if item["ranking"] <= parsed_quota:
                item["status_sistem"] = "layak"
            elif item["ranking"] <= parsed_quota + parsed_reserve:
                item["status_sistem"] = "cadangan"
            else:
                item["status_sistem"] = "tidak_layak"

        item["status_final"] = item["status_sistem"]

    return hasil


def simpan_riwayat_perhitungan(data: Dict[str, Any], jumlah_data: int):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        riwayat_id = bikin_uuid()

        cur.execute(
            """
            INSERT INTO riwayat_perhitungan (
                id,
                nama_perhitungan,
                metode,
                jumlah_data,
                consistency_ratio,
                mode_status,
                threshold,
                kuota,
                reserve_quota,
                dihitung_oleh,
                tanggal_hitung
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            RETURNING
                id,
                nama_perhitungan,
                metode,
                jumlah_data,
                consistency_ratio,
                mode_status,
                threshold,
                kuota,
                reserve_quota,
                dihitung_oleh,
                tanggal_hitung
            """,
            (
                riwayat_id,
                data.get("nama_perhitungan"),
                "AHP-SAW",
                jumlah_data,
                data.get("consistency_ratio"),
                data.get("mode"),
                data.get("threshold"),
                data.get("quota"),
                data.get("reserve_quota"),
                normalisasi_uuid(data.get("dihitung_oleh")),
            ),
        )

        row = normalize_row(cur.fetchone())
        conn.commit()

        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        riwayat_id = bikin_uuid()

        cur.execute(
            """
            INSERT INTO riwayat_perhitungan (
                id,
                nama_perhitungan,
                metode,
                jumlah_data,
                mode_status,
                threshold,
                kuota,
                dihitung_oleh,
                tanggal_hitung
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            RETURNING
                id,
                nama_perhitungan,
                metode,
                jumlah_data,
                consistency_ratio,
                mode_status,
                threshold,
                kuota,
                dihitung_oleh,
                tanggal_hitung
            """,
            (
                riwayat_id,
                data.get("nama_perhitungan"),
                "AHP-SAW",
                jumlah_data,
                data.get("mode"),
                data.get("threshold"),
                data.get("quota"),
                normalisasi_uuid(data.get("dihitung_oleh")),
            ),
        )

        row = normalize_row(cur.fetchone())
        conn.commit()

        return row

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def hapus_hasil_lama():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM hasil_spk")
        conn.commit()

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def simpan_hasil_spk(riwayat_id: str, hasil: List[Dict[str, Any]]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        saved = []

        for item in hasil:
            hasil_id = bikin_uuid()

            cur.execute(
                """
                INSERT INTO hasil_spk (
                    id,
                    riwayat_perhitungan_id,
                    keluarga_id,
                    total_nilai,
                    ranking,
                    status_sistem,
                    status_final,
                    tanggal_hitung
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
                RETURNING
                    id,
                    riwayat_perhitungan_id,
                    keluarga_id,
                    total_nilai,
                    ranking,
                    status_sistem,
                    status_final,
                    tanggal_hitung
                """,
                (
                    hasil_id,
                    riwayat_id,
                    item["keluarga_id"],
                    item["total_nilai"],
                    item["ranking"],
                    item["status_sistem"],
                    item["status_final"],
                ),
            )

            saved.append(normalize_row(cur.fetchone()))

        conn.commit()

        return saved

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def hitung_saw_dari_database(data: Dict[str, Any]):
    mode = data.get("mode") or "kuota"
    quota = data.get("quota")
    reserve_quota = data.get("reserve_quota") or 0
    threshold = data.get("threshold")

    kriteria = ambil_kriteria_aktif()

    if not kriteria:
        raise ValueError("Belum ada kriteria aktif.")

    total_bobot = sum(to_float(item.get("bobot_ahp")) for item in kriteria)
    if abs(total_bobot - 1.0) > 0.01:
        raise ValueError(
            f"Total bobot AHP harus mendekati 1. Total bobot saat ini: {total_bobot:.6f}"
        )

    if total_bobot <= 0:
        raise ValueError("Total bobot kriteria masih 0. Isi bobot AHP terlebih dahulu.")

    rows = ambil_data_penilaian_terverifikasi()

    if not rows:
        raise ValueError(
            "Belum ada data penilaian untuk keluarga terverifikasi. "
            "Pastikan data warga sudah terverifikasi dan penilaian C1-C6 sudah tersimpan."
        )

    keluarga_lengkap, keluarga_tidak_lengkap = bentuk_matrix_penilaian(rows, kriteria)

    if not keluarga_lengkap:
        raise ValueError(
            "Tidak ada keluarga dengan penilaian lengkap sesuai kriteria aktif."
        )

    if mode == "kuota":
        if quota is None or int(quota) <= 0:
            raise ValueError("Mode kuota membutuhkan quota minimal 1.")

    if mode == "threshold":
        if threshold is None:
            raise ValueError("Mode threshold membutuhkan nilai threshold.")

    hasil_normalisasi = normalisasi_saw(keluarga_lengkap, kriteria)

    hasil_status = tentukan_status(
        hasil=hasil_normalisasi,
        mode=mode,
        threshold=threshold,
        quota=quota,
        reserve_quota=reserve_quota,
    )

    riwayat = simpan_riwayat_perhitungan(
        data=data,
        jumlah_data=len(hasil_status),
    )

    saved = simpan_hasil_spk(riwayat["id"], hasil_status)

    return {
        "message": "Perhitungan SAW berhasil dijalankan.",
        "riwayat": riwayat,
        "data": hasil_status,
        "saved": saved,
        "keluarga_tidak_lengkap": keluarga_tidak_lengkap,
    }


def ambil_hasil_terbaru():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            WITH latest_riwayat AS (
                SELECT id
                FROM riwayat_perhitungan
                ORDER BY tanggal_hitung DESC
                LIMIT 1
            )
            SELECT
                h.id,
                h.riwayat_perhitungan_id,
                h.keluarga_id,
                k.nama_kepala_keluarga,
                k.nik,
                k.kelurahan,
                k.dusun,
                h.total_nilai,
                h.ranking,
                h.status_sistem,
                h.status_final,
                h.tanggal_hitung
            FROM hasil_spk h
            JOIN keluarga k ON k.id = h.keluarga_id
            JOIN latest_riwayat lr ON lr.id = h.riwayat_perhitungan_id
            ORDER BY h.ranking ASC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                h.id,
                h.riwayat_perhitungan_id,
                h.keluarga_id,
                k.nama_kepala_keluarga,
                k.nik,
                k.kelurahan,
                k.dusun,
                h.total_nilai,
                h.ranking,
                h.status_sistem,
                h.status_final,
                h.tanggal_hitung
            FROM hasil_spk h
            JOIN keluarga k ON k.id = h.keluarga_id
            ORDER BY h.ranking ASC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()


def ambil_riwayat():
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
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
                dihitung_oleh,
                tanggal_hitung
            FROM riwayat_perhitungan
            ORDER BY tanggal_hitung DESC
            """
        )

        return normalize_rows(cur.fetchall())

    finally:
        cur.close()
        conn.close()