from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Dict, Optional


"""
Mapping skor SIMNAKIS/BPS untuk auto-generate penilaian C1-C10.

Prinsip skor:
- 5 = kondisi paling miskin / paling layak menerima bantuan
- 1 = kondisi paling mampu / paling tidak prioritas

Catatan:
Dataset SIMNAKIS yang kamu upload memakai kode angka pada banyak kolom.
Mapping ini dibuat berdasarkan pola kode umum BPS/SIMNAKIS.
Kalau nanti kamu punya kodebook resmi dari dataset, cukup ubah dictionary di file ini.
"""


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    if text.lower() in ["nan", "none", "null", "-", "tidak ada data"]:
        return None

    return text


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, float) and math.isnan(value):
        return None

    try:
        text = str(value).strip().replace(",", ".")

        if text == "":
            return None

        return float(text)

    except Exception:
        return None


def to_int(value: Any) -> Optional[int]:
    parsed = to_float(value)

    if parsed is None:
        return None

    return int(parsed)


def nilai_ya_tidak(value: Any) -> int:
    """
    Normalisasi nilai kepemilikan.

    Di dataset SIMNAKIS kamu, kode kepemilikan tidak selalu 1/2.
    Pola yang terlihat:
    - ada_sepeda: 1/2
    - ada_mobil, ada_ac, ada_emas, aset_tak_bergerak: 1/2
    - ada_motor, ada_lemari_es, ada_tv, ada_laptop, rumah_lain: 3/4

    Mapping konservatif:
    - 1 atau 3 = punya/ada
    - 2 atau 4 = tidak punya/tidak ada
    """

    kode = to_int(value)

    if kode in [1, 3]:
        return 1

    if kode in [2, 4, 0]:
        return 0

    text = (clean_text(value) or "").lower()

    if text in ["1", "3", "ya", "y", "true", "ada", "punya", "memiliki"]:
        return 1

    return 0


def score_jumlah_anggota(value: Any) -> float:
    jumlah = to_int(value) or 1

    if jumlah >= 6:
        return 5
    if jumlah >= 4:
        return 4
    if jumlah == 3:
        return 3
    if jumlah == 2:
        return 2

    return 1


def score_luas_lantai(value: Any) -> float:
    """
    C2 adalah cost criteria.
    Semakin kecil luas lantai, semakin prioritas.
    Nilai asli luas lantai tetap dipakai agar normalisasi SAW cost = min / nilai.
    """

    luas = to_float(value)

    if luas is None or luas <= 0:
        return 5

    return luas


def score_lantai(value: Any) -> float:
    kode = to_int(value)

    # Kode umum BPS/SIMNAKIS jenis lantai terluas.
    # 1 marmer/granit, 2 keramik, 3 parket/vinil/permadani,
    # 4 ubin/tegel/teraso, 5 kayu/papan kualitas tinggi,
    # 6 semen/bata merah, 7 bambu, 8 kayu/papan kualitas rendah,
    # 9 tanah, 10 lainnya.
    by_code = {
        1: 1,
        2: 2,
        3: 2,
        4: 3,
        5: 3,
        6: 4,
        7: 5,
        8: 4,
        9: 5,
        10: 3,
    }

    if kode in by_code:
        return float(by_code[kode])

    text = (clean_text(value) or "").lower()

    if "tanah" in text:
        return 5
    if "bambu" in text:
        return 5
    if "semen" in text or "plester" in text or "bata" in text:
        return 4
    if "kayu" in text or "papan" in text:
        return 3
    if "ubin" in text or "tegel" in text or "teraso" in text:
        return 3
    if "keramik" in text:
        return 2
    if "marmer" in text or "granit" in text:
        return 1

    return 3


def score_dinding(dinding: Any, kondisi_dinding: Any = None) -> float:
    kode_kondisi = to_int(kondisi_dinding)

    # Umumnya: 1 = bagus/baik, 2 = jelek/rusak/kualitas rendah.
    kondisi_score = None
    if kode_kondisi == 1:
        kondisi_score = 1
    elif kode_kondisi == 2:
        kondisi_score = 4
    elif kode_kondisi == 3:
        kondisi_score = 5

    kode_dinding = to_int(dinding)

    # Kode umum jenis dinding terluas:
    # 1 tembok, 2 plesteran anyaman bambu/kawat, 3 kayu,
    # 4 anyaman bambu, 5 batang kayu, 6 bambu, 7 lainnya.
    by_code = {
        1: 1,
        2: 3,
        3: 3,
        4: 5,
        5: 4,
        6: 5,
        7: 3,
    }

    material_score = by_code.get(kode_dinding)

    if kondisi_score is not None and material_score is not None:
        return float(max(kondisi_score, material_score))

    if kondisi_score is not None:
        return float(kondisi_score)

    if material_score is not None:
        return float(material_score)

    text = f"{clean_text(dinding) or ''} {clean_text(kondisi_dinding) or ''}".lower()

    if "rusak berat" in text or "buruk" in text or "jelek" in text:
        return 5
    if "bambu" in text or "anyaman" in text:
        return 5
    if "batang kayu" in text:
        return 4
    if "rusak sedang" in text:
        return 4
    if "kayu" in text or "papan" in text:
        return 3
    if "rusak ringan" in text or "plester" in text:
        return 3
    if "tembok" in text or "baik" in text:
        return 1

    return 3


def score_atap(atap: Any, kondisi_atap: Any = None) -> float:
    kode_kondisi = to_int(kondisi_atap)

    kondisi_score = None
    if kode_kondisi == 1:
        kondisi_score = 1
    elif kode_kondisi == 2:
        kondisi_score = 4
    elif kode_kondisi == 3:
        kondisi_score = 5

    kode_atap = to_int(atap)

    # Kode umum jenis atap terluas.
    # Semakin sederhana/rentan, skor semakin tinggi.
    by_code = {
        1: 1,   # beton
        2: 2,   # genteng
        3: 3,   # seng
        4: 3,   # asbes
        5: 4,   # bambu/kayu/sirap
        6: 5,   # jerami/ijuk/daun/rumbia atau material sangat sederhana
        7: 5,
        8: 4,
        9: 3,
        10: 3,
    }

    material_score = by_code.get(kode_atap)

    if kondisi_score is not None and material_score is not None:
        return float(max(kondisi_score, material_score))

    if kondisi_score is not None:
        return float(kondisi_score)

    if material_score is not None:
        return float(material_score)

    text = f"{clean_text(atap) or ''} {clean_text(kondisi_atap) or ''}".lower()

    if "rusak berat" in text or "buruk" in text or "jelek" in text:
        return 5
    if "rumbia" in text or "daun" in text or "ijuk" in text or "jerami" in text:
        return 5
    if "bambu" in text or "sirap" in text:
        return 4
    if "rusak sedang" in text:
        return 4
    if "asbes" in text or "seng" in text:
        return 3
    if "genteng" in text:
        return 2
    if "beton" in text or "baik" in text:
        return 1

    return 3


def score_sumber_air(value: Any) -> float:
    kode = to_int(value)

    # Kode umum sumber air minum:
    # 1 air kemasan, 2 isi ulang, 3 ledeng meteran, 4 ledeng eceran,
    # 5 sumur bor/pompa, 6 sumur terlindung, 7 sumur tak terlindung,
    # 8 mata air terlindung, 9 mata air tak terlindung,
    # 10 air permukaan, 11 air hujan, 12 lainnya.
    by_code = {
        1: 1,
        2: 1,
        3: 2,
        4: 2,
        5: 3,
        6: 3,
        7: 4,
        8: 3,
        9: 4,
        10: 5,
        11: 5,
        12: 5,
    }

    if kode in by_code:
        return float(by_code[kode])

    text = (clean_text(value) or "").lower()

    if "sungai" in text or "hujan" in text or "danau" in text or "permukaan" in text:
        return 5
    if "tak terlindung" in text or "tidak terlindung" in text:
        return 4
    if "sumur" in text or "mata air" in text:
        return 3
    if "ledeng" in text or "pdam" in text:
        return 2
    if "kemasan" in text or "isi ulang" in text:
        return 1

    return 3


def score_daya_listrik(daya: Any, sumber_penerangan: Any = None) -> float:
    kode_sumber = to_int(sumber_penerangan)

    # Umumnya: 1 listrik PLN, 2 listrik non PLN, 3 bukan listrik.
    if kode_sumber == 3:
        return 5

    sumber_text = (clean_text(sumber_penerangan) or "").lower()
    if "bukan listrik" in sumber_text or "tidak" in sumber_text:
        return 5

    kode_daya = to_int(daya)

    # Kode daya dataset SIMNAKIS biasanya berupa kategori, bukan watt mentah.
    # 1=450 VA, 2=900 VA, 3=1300 VA, 4=2200 VA, 5=>2200 VA, 6=tanpa meteran/tidak diketahui.
    by_code = {
        1: 4,
        2: 3,
        3: 2,
        4: 1,
        5: 1,
        6: 4,
    }

    if kode_daya in by_code:
        return float(by_code[kode_daya])

    daya_float = to_float(daya)

    if daya_float is None or daya_float <= 0:
        return 5
    if daya_float <= 450:
        return 4
    if daya_float <= 900:
        return 3
    if daya_float <= 1300:
        return 2

    return 1


def score_fasilitas_bab(fas_bab: Any, kloset: Any = None) -> float:
    kode_fas = to_int(fas_bab)

    # Kode umum fasilitas BAB:
    # 1 sendiri, 2 bersama, 3 umum, 4 tidak ada.
    by_fas_code = {
        1: 1,
        2: 3,
        3: 4,
        4: 5,
    }

    if kode_fas in by_fas_code:
        return float(by_fas_code[kode_fas])

    kode_kloset = to_int(kloset)

    # Kode umum kloset:
    # 1 leher angsa, 2 plengsengan, 3 cemplung/cubluk, 4 tidak pakai.
    by_kloset_code = {
        1: 1,
        2: 3,
        3: 4,
        4: 5,
    }

    if kode_kloset in by_kloset_code:
        return float(by_kloset_code[kode_kloset])

    fas = (clean_text(fas_bab) or "").lower()
    klo = (clean_text(kloset) or "").lower()

    if "tidak" in fas or "tidak ada" in klo or "cemplung" in klo or "cubluk" in klo:
        return 5
    if "umum" in fas:
        return 4
    if "bersama" in fas:
        return 3
    if "sendiri" in fas or "leher angsa" in klo:
        return 1

    return 3


def score_kendaraan(row: Dict[str, Any]) -> float:
    sepeda = nilai_ya_tidak(row.get("ada_sepeda"))
    motor = nilai_ya_tidak(row.get("ada_motor"))
    mobil = nilai_ya_tidak(row.get("ada_mobil"))

    if mobil:
        return 1
    if motor:
        return 2
    if sepeda:
        return 3

    return 5


def score_aset(row: Dict[str, Any]) -> float:
    aset_columns = [
        "ada_lemari_es",
        "ada_ac",
        "ada_tv",
        "ada_emas",
        "ada_laptop",
        "aset_tak_bergerak",
        "rumah_lain",
    ]

    jumlah_aset = sum(nilai_ya_tidak(row.get(col)) for col in aset_columns)

    jumlah_ternak = 0
    for col in [
        "jumlah_sapi",
        "jumlah_kerbau",
        "jumlah_kuda",
        "jumlah_babi",
        "jumlah_kambing",
    ]:
        jumlah_ternak += to_int(row.get(col)) or 0

    if jumlah_aset >= 4 or jumlah_ternak >= 5:
        return 1
    if jumlah_aset >= 2 or jumlah_ternak >= 2:
        return 2
    if jumlah_aset == 1 or jumlah_ternak == 1:
        return 3

    return 5


def hitung_skor_simnangkis(row: Dict[str, Any]) -> Dict[str, float]:
    return {
        "C1": score_jumlah_anggota(row.get("jml_anggota_keluarga")),
        "C2": score_luas_lantai(row.get("luas_lantai")),
        "C3": score_lantai(row.get("lantai")),
        "C4": score_dinding(row.get("dinding"), row.get("kondisi_dinding")),
        "C5": score_atap(row.get("atap"), row.get("kondisi_atap")),
        "C6": score_sumber_air(row.get("sumber_air_minum")),
        "C7": score_daya_listrik(row.get("daya"), row.get("sumber_penerangan")),
        "C8": score_fasilitas_bab(row.get("fas_bab"), row.get("kloset")),
        "C9": score_kendaraan(row),
        "C10": score_aset(row),
    }
