from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PenilaianSawItemRequest(BaseModel):
    keluarga_id: str
    kriteria_id: str
    sub_kriteria_id: Optional[str] = None
    nilai_awal: float


class SimpanPenilaianSawRequest(BaseModel):
    data: List[PenilaianSawItemRequest]


class SawCalculateFromDbRequest(BaseModel):
    nama_perhitungan: str = Field(..., min_length=1)
    mode: str = Field(default="kuota", pattern="^(threshold|kuota)$")
    threshold: Optional[float] = None
    quota: Optional[int] = None
    reserve_quota: Optional[int] = 0
    dihitung_oleh: Optional[str] = None


class AutoGeneratePenilaianImportRequest(BaseModel):
    import_batch_id: str


class SawResultResponse(BaseModel):
    id: Optional[str] = None
    keluarga_id: str
    nama_kepala_keluarga: str
    nik: str
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    total_nilai: float | str
    ranking: int
    status_sistem: str
    status_final: Optional[str] = None
    tanggal_hitung: Optional[Any] = None
    riwayat_perhitungan_id: Optional[str] = None


class RiwayatSawResponse(BaseModel):
    id: str
    nama_perhitungan: str
    metode: str
    jumlah_data: int
    consistency_ratio: Optional[float | str] = None
    mode_status: str
    threshold: Optional[float | str] = None
    kuota: Optional[int] = None
    tanggal_hitung: Any
    dihitung_oleh: Optional[str] = None