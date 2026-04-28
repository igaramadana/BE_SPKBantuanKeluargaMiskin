from fastapi import HTTPException
from typing import List, Dict, Any
from app.modules.saw import repository


MODE_VALID = ["threshold", "kuota"]


def normalin_saw(alternatif: List[Dict[str, Any]], kriteria: List[Dict[str, Any]]):
    for item_kriteria in kriteria:
        kode = item_kriteria["kode"]
        jenis = item_kriteria["jenis"]

        nilai_list = [
            float(item["nilai"][kode])
            for item in alternatif
            if kode in item["nilai"] and item["nilai"][kode] is not None
        ]

        if not nilai_list:
            raise ValueError(f"Nilai untuk kriteria {kode} belum ada.")

        nilai_max = max(nilai_list)
        nilai_min = min(nilai_list)

        for item in alternatif:
            if kode not in item["nilai"]:
                raise ValueError(f"Keluarga {item['keluarga_id']} belum punya nilai {kode}.")

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


def kasih_status_threshold(hasil_rank, threshold: float):
    for item in hasil_rank:
        item["status"] = "layak" if item["total_nilai"] >= threshold else "tidak_layak"

    return hasil_rank


def kasih_status_kuota(hasil_rank, kuota: int, kuota_cadangan: int = 0):
    for item in hasil_rank:
        if item["ranking"] <= kuota:
            item["status"] = "layak"
        elif kuota_cadangan > 0 and item["ranking"] <= kuota + kuota_cadangan:
            item["status"] = "cadangan"
        else:
            item["status"] = "tidak_layak"

    return hasil_rank


def validasi_mode(mode: str, threshold=None, quota=None):
    if mode not in MODE_VALID:
        raise HTTPException(status_code=400, detail="Mode harus threshold atau kuota.")

    if mode == "threshold" and threshold is None:
        raise HTTPException(status_code=400, detail="Threshold wajib diisi.")

    if mode == "kuota" and quota is None:
        raise HTTPException(status_code=400, detail="Kuota wajib diisi.")


def gas_hitung_manual(payload):
    try:
        validasi_mode(payload.mode, payload.threshold, payload.quota)

        alternatif = [item.model_dump() for item in payload.alternatives]
        kriteria = [item.model_dump() for item in payload.criteria]

        hasil = gas_hitung_saw(alternatif, kriteria)

        if payload.mode == "threshold":
            hasil = kasih_status_threshold(hasil, payload.threshold)

        if payload.mode == "kuota":
            hasil = kasih_status_kuota(
                hasil,
                payload.quota,
                payload.reserve_quota or 0,
            )

        return {
            "message": "Perhitungan SAW manual berhasil.",
            "data": hasil,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_simpan_penilaian(payload):
    data = [item.model_dump() for item in payload.data]

    if not data:
        raise HTTPException(status_code=400, detail="Data penilaian kosong.")

    try:
        hasil = repository.simpan_penilaian_batch(data)

        return {
            "message": "Penilaian berhasil disimpan.",
            "data": hasil,
        }

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def bentuk_data_saw_dari_database():
    kriteria = repository.ambil_kriteria_aktif_dengan_bobot()
    keluarga = repository.ambil_keluarga_terverifikasi()
    penilaian = repository.ambil_penilaian_aktif()

    if not kriteria:
        raise HTTPException(status_code=400, detail="Belum ada kriteria aktif.")

    for item in kriteria:
        if item["bobot_ahp"] is None:
            raise HTTPException(
                status_code=400,
                detail=f"Kriteria {item['kode']} belum punya bobot AHP.",
            )

    if not keluarga:
        raise HTTPException(status_code=400, detail="Belum ada keluarga terverifikasi.")

    nilai_by_keluarga = {}

    for item in keluarga:
        nilai_by_keluarga[item["id"]] = {
            "keluarga_id": item["id"],
            "nama_kepala_keluarga": item["nama_kepala_keluarga"],
            "nik": item["nik"],
            "kelurahan": item["kelurahan"],
            "dusun": item["dusun"],
            "nilai": {},
        }

    for item in penilaian:
        keluarga_id = item["keluarga_id"]

        if keluarga_id in nilai_by_keluarga:
            nilai_by_keluarga[keluarga_id]["nilai"][item["kode_kriteria"]] = float(item["nilai_awal"])

    alternatif = list(nilai_by_keluarga.values())

    kode_kriteria = [item["kode"] for item in kriteria]

    for item in alternatif:
        for kode in kode_kriteria:
            if kode not in item["nilai"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Keluarga {item['nama_kepala_keluarga']} belum punya penilaian untuk {kode}.",
                )

    data_kriteria = [
        {
            "id": item["id"],
            "kode": item["kode"],
            "nama": item["nama"],
            "jenis": item["jenis"],
            "bobot_ahp": float(item["bobot_ahp"]),
        }
        for item in kriteria
    ]

    return alternatif, data_kriteria


def gas_hitung_dari_database(payload):
    validasi_mode(payload.mode, payload.threshold, payload.quota)

    try:
        alternatif, kriteria = bentuk_data_saw_dari_database()

        hasil = gas_hitung_saw(alternatif, kriteria)

        if payload.mode == "threshold":
            hasil = kasih_status_threshold(hasil, payload.threshold)

        if payload.mode == "kuota":
            hasil = kasih_status_kuota(
                hasil,
                payload.quota,
                payload.reserve_quota or 0,
            )

        riwayat = repository.bikin_riwayat_perhitungan(
            nama_perhitungan=payload.nama_perhitungan,
            jumlah_data=len(hasil),
            mode_status=payload.mode,
            threshold=payload.threshold,
            kuota=payload.quota,
            dihitung_oleh=payload.dihitung_oleh,
        )

        for item in hasil:
            for kode, nilai_normalisasi in item["normalisasi"].items():
                nilai_terbobot = item["nilai_terbobot"][kode]

                repository.update_penilaian_hasil(
                    keluarga_id=item["keluarga_id"],
                    kode_kriteria=kode,
                    nilai_normalisasi=nilai_normalisasi,
                    nilai_terbobot=nilai_terbobot,
                )

        hasil_simpan = repository.simpan_hasil_spk_batch(
            riwayat_id=riwayat["id"],
            data=hasil,
        )

        return {
            "message": "Perhitungan SAW dari database berhasil dan sudah disimpan.",
            "riwayat": riwayat,
            "data": hasil,
            "saved": hasil_simpan,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


def gas_ambil_hasil_terbaru():
    return repository.ambil_hasil_spk_terbaru()


def gas_ambil_riwayat():
    return repository.ambil_riwayat_perhitungan()


def gas_ambil_hasil_by_riwayat(riwayat_id: str):
    hasil = repository.ambil_hasil_by_riwayat(riwayat_id)

    if not hasil:
        raise HTTPException(
            status_code=404,
            detail="Hasil perhitungan tidak ditemukan.",
        )

    return hasil