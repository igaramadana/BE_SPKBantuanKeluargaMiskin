from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class KriteriaCreate(BaseModel):
    kode: str
    nama: str
    jenis: str
    aktif: bool = True
    urutan: Optional[int] = None

class KriteriaUpdate(BaseModel):
    kode: Optional[str] = None
    nama: Optional[str] = None
    jenis: Optional[str] = None
    aktif: Optional[bool] = None
    urutan: Optional[int] = None
    bobot_ahp: Optional[Decimal] = None