from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SawAlternative(BaseModel):
    keluarga_id: str
    nama_kepala_keluarga: str
    nilai: Dict[str, float]


class SawCriterion(BaseModel):
    kode: str
    jenis: str
    bobot_ahp: float


class SawCalculateRequest(BaseModel):
    alternatives: List[SawAlternative]
    criteria: List[SawCriterion]
    mode: str = Field(..., description="threshold atau kuota")
    threshold: Optional[float] = None
    quota: Optional[int] = None
    reserve_quota: Optional[int] = 0


class SawFromDatabaseRequest(BaseModel):
    nama_perhitungan: str = "Perhitungan AHP-SAW"
    mode: str = Field(..., description="threshold atau kuota")
    threshold: Optional[float] = None
    quota: Optional[int] = None
    reserve_quota: Optional[int] = 0
    dihitung_oleh: Optional[str] = None


class MappingPenilaianItem(BaseModel):
    keluarga_id: str
    kriteria_id: str
    sub_kriteria_id: Optional[str] = None
    nilai_awal: float


class SimpanPenilaianRequest(BaseModel):
    data: List[MappingPenilaianItem]