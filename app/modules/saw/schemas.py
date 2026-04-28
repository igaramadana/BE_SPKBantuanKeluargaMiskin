from typing import List, Dict, Any


def normalin_saw(alternatif: List[Dict[str, Any]], kriteria: List[Dict[str, Any]]):
    for item_kriteria in kriteria:
        kode = item_kriteria["kode"]
        jenis = item_kriteria["jenis"]

        nilai_list = [
            float(item["nilai"][kode])
            for item in alternatif
            if kode in item["nilai"] and item["nilai"][kode] is not None
        ]

        nilai_max = max(nilai_list)
        nilai_min = min(nilai_list)

        for item in alternatif:
            if "normalisasi" not in item:
                item["normalisasi"] = {}

            nilai_awal = float(item["nilai"][kode])

            if jenis == "benefit":
                nilai_normal = nilai_awal / nilai_max if nilai_max else 0
            elif jenis == "cost":
                nilai_normal = nilai_min / nilai_awal if nilai_awal else 0
            else:
                raise ValueError("Jenis kriteria harus benefit atau cost.")

            item["normalisasi"][kode] = nilai_normal

    return alternatif


def gas_hitung_saw(alternatif: List[Dict[str, Any]], kriteria: List[Dict[str, Any]]):
    data_normal = normalin_saw(alternatif, kriteria)

    for item in data_normal:
        total = 0
        item["nilai_terbobot"] = {}

        for item_kriteria in kriteria:
            kode = item_kriteria["kode"]
            bobot = float(item_kriteria["bobot_ahp"])
            nilai_normal = item["normalisasi"][kode]
            nilai_terbobot = nilai_normal * bobot

            item["nilai_terbobot"][kode] = nilai_terbobot
            total += nilai_terbobot

        item["total_nilai"] = total

    hasil_rank = sorted(data_normal, key=lambda x: x["total_nilai"], reverse=True)

    for index, item in enumerate(hasil_rank, start=1):
        item["ranking"] = index

    return hasil_rank