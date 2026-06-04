from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SubKriteriaResponse(BaseModel):
    id: str
    kriteria_id: str
    nama: str
    nilai: float | int
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class KriteriaCreateRequest(BaseModel):
    kode: str = Field(..., min_length=1)
    nama: str = Field(..., min_length=1)
    jenis: str = Field(..., pattern="^(benefit|cost)$")
    aktif: bool = True
    urutan: Optional[int] = None


class KriteriaUpdateRequest(BaseModel):
    kode: Optional[str] = None
    nama: Optional[str] = None
    jenis: Optional[str] = Field(default=None, pattern="^(benefit|cost)$")
    bobot_ahp: Optional[float] = None
    aktif: Optional[bool] = None
    urutan: Optional[int] = None


class KriteriaResponse(BaseModel):
    id: str
    kode: str
    nama: str
    jenis: str
    bobot_ahp: Optional[float] = None
    aktif: bool
    urutan: Optional[int] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    sub_kriteria: Optional[List[SubKriteriaResponse]] = None