from typing import List, Dict, Any
import numpy as np


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
}


def hitung_ahp(matrix: List[List[float]]) -> Dict[str, Any]:
    matriks = np.array(matrix, dtype=float)

    if matriks.shape[0] != matriks.shape[1]:
        raise ValueError("Matriks AHP harus persegi.")

    jumlah_kriteria = matriks.shape[0]
    total_kolom = matriks.sum(axis=0)

    if np.any(total_kolom == 0):
        raise ValueError("Total kolom tidak boleh nol.")

    matriks_normal = matriks / total_kolom
    bobot = matriks_normal.mean(axis=1)

    weighted_sum = matriks @ bobot
    lambda_values = weighted_sum / bobot
    lambda_max = lambda_values.mean()

    ci = (lambda_max - jumlah_kriteria) / (jumlah_kriteria - 1)
    ri = RI_TABLE.get(jumlah_kriteria)

    if ri is None:
        raise ValueError("RI untuk jumlah kriteria ini belum tersedia.")

    cr = 0 if ri == 0 else ci / ri

    return {
        "weights": bobot.tolist(),
        "lambda_max": float(lambda_max),
        "ci": float(ci),
        "cr": float(cr),
        "is_consistent": bool(cr <= 0.1),
        "normalized_matrix": matriks_normal.tolist(),
    }