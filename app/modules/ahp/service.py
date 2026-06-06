from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import HTTPException

from app.db.connection import ambil_koneksi


RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.59,
}


def bikin_uuid() -> str:
    return str(uuid4())


def to_float(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, Decimal):
        return float(value)

    try:
        return float(value)
    except Exception:
        return 0.0


def normalize_row(row):
    if row is None:
        return None

    result = {}

    for key, value in dict(row).items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value

    return result


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
                bobot_ahp,
                aktif,
                urutan
            FROM kriteria
            WHERE aktif = true
            ORDER BY urutan ASC NULLS LAST, kode ASC
            """
        )

        return [normalize_row(row) for row in cur.fetchall()]

    finally:
        cur.close()
        conn.close()


def simpan_perbandingan_ahp(perbandingan):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        for item in perbandingan:
            cur.execute(
                """
                INSERT INTO ahp_perbandingan (
                    id,
                    kriteria_1_id,
                    kriteria_2_id,
                    nilai,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (kriteria_1_id, kriteria_2_id)
                DO UPDATE SET
                    nilai = EXCLUDED.nilai,
                    updated_at = NOW()
                """,
                (
                    bikin_uuid(),
                    item.kriteria_1_id,
                    item.kriteria_2_id,
                    item.nilai,
                ),
            )

        conn.commit()

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def simpan_bobot_kriteria(weights: List[Dict[str, Any]]):
    conn = ambil_koneksi()
    cur = conn.cursor()

    try:
        for item in weights:
            cur.execute(
                """
                UPDATE kriteria
                SET
                    bobot_ahp = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    item["bobot"],
                    item["kriteria_id"],
                ),
            )

        conn.commit()

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def bikin_matrix(kriteria: List[Dict[str, Any]], perbandingan) -> List[List[float]]:
    n = len(kriteria)
    index_by_id = {item["id"]: index for index, item in enumerate(kriteria)}

    matrix = [[1.0 for _ in range(n)] for _ in range(n)]

    for item in perbandingan:
        kriteria_1_id = item.kriteria_1_id
        kriteria_2_id = item.kriteria_2_id
        nilai = float(item.nilai)

        if kriteria_1_id not in index_by_id:
            raise ValueError(f"Kriteria 1 tidak aktif/tidak ditemukan: {kriteria_1_id}")

        if kriteria_2_id not in index_by_id:
            raise ValueError(f"Kriteria 2 tidak aktif/tidak ditemukan: {kriteria_2_id}")

        i = index_by_id[kriteria_1_id]
        j = index_by_id[kriteria_2_id]

        matrix[i][j] = nilai
        matrix[j][i] = 1.0 / nilai

    return matrix


def hitung_ahp_matrix(matrix: List[List[float]]):
    n = len(matrix)

    if n == 0:
        raise ValueError("Matrix kosong.")

    if n == 1:
        return {
            "weights": [1.0],
            "lambda_max": 1.0,
            "consistency_index": 0.0,
            "consistency_ratio": 0.0,
            "is_consistent": True,
            "normalized_matrix": [[1.0]],
            "column_sums": [1.0],
        }

    column_sums = []

    for col in range(n):
        total = sum(matrix[row][col] for row in range(n))
        column_sums.append(total)

    normalized_matrix = []

    for row in range(n):
        normalized_row = []

        for col in range(n):
            if column_sums[col] == 0:
                normalized_row.append(0.0)
            else:
                normalized_row.append(matrix[row][col] / column_sums[col])

        normalized_matrix.append(normalized_row)

    weights = []

    for row in normalized_matrix:
        weights.append(sum(row) / n)

    weighted_sum_vector = []

    for i in range(n):
        total = 0.0

        for j in range(n):
            total += matrix[i][j] * weights[j]

        weighted_sum_vector.append(total)

    lambda_values = []

    for i in range(n):
        if weights[i] == 0:
            lambda_values.append(0.0)
        else:
            lambda_values.append(weighted_sum_vector[i] / weights[i])

    lambda_max = sum(lambda_values) / n
    consistency_index = (lambda_max - n) / (n - 1)

    ri = RI_TABLE.get(n)

    if ri is None:
        ri = 1.59

    if ri == 0:
        consistency_ratio = 0.0
    else:
        consistency_ratio = consistency_index / ri

    return {
        "weights": weights,
        "lambda_max": lambda_max,
        "consistency_index": consistency_index,
        "consistency_ratio": consistency_ratio,
        "is_consistent": consistency_ratio <= 0.1,
        "normalized_matrix": normalized_matrix,
        "column_sums": column_sums,
    }


def gas_hitung_ahp(payload):
    try:
        kriteria = ambil_kriteria_aktif()

        if not kriteria:
            raise ValueError("Belum ada kriteria aktif.")

        if len(kriteria) < 2:
            raise ValueError("Minimal butuh 2 kriteria aktif untuk AHP.")

        expected_pairs = len(kriteria) * (len(kriteria) - 1) // 2

        if len(payload.perbandingan) < expected_pairs:
            raise ValueError(
                f"Perbandingan belum lengkap. Dibutuhkan {expected_pairs} pasangan."
            )

        matrix = bikin_matrix(kriteria, payload.perbandingan)
        ahp_result = hitung_ahp_matrix(matrix)

        weights = []

        for index, item in enumerate(kriteria):
            weights.append(
                {
                    "kriteria_id": item["id"],
                    "kode": item.get("kode"),
                    "nama": item.get("nama"),
                    "bobot": round(ahp_result["weights"][index], 6),
                }
            )

        simpan_perbandingan_ahp(payload.perbandingan)

        if payload.simpan_bobot:
            if not ahp_result["is_consistent"]:
                raise ValueError(
                    "Matrix AHP belum konsisten. Consistency Ratio harus <= 0.1."
                )

            simpan_bobot_kriteria(weights)

        return {
            "message": (
                "Bobot AHP berhasil dihitung dan disimpan."
                if payload.simpan_bobot
                else "Bobot AHP berhasil dihitung."
            ),
            "weights": weights,
            "lambda_max": round(ahp_result["lambda_max"], 6),
            "consistency_index": round(ahp_result["consistency_index"], 6),
            "consistency_ratio": round(ahp_result["consistency_ratio"], 6),
            "is_consistent": ahp_result["is_consistent"],
            "data": {
                "matrix": matrix,
                "normalized_matrix": ahp_result["normalized_matrix"],
                "column_sums": ahp_result["column_sums"],
            },
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )