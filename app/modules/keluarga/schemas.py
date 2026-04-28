from pydantic import BaseModel, Field
from typing import Optional


class KeluargaCreate(BaseModel):
    user_id: Optional[str] = None
    nama_kepala_keluarga: str = Field(..., min_length=2)
    nik: str = Field(..., min_length=8)
    alamat: Optional[str] = None
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    jumlah_anggota: Optional[int] = Field(default=None, ge=1)
    created_by: Optional[str] = None


class KeluargaUpdate(BaseModel):
    user_id: Optional[str] = None
    nama_kepala_keluarga: Optional[str] = Field(default=None, min_length=2)
    nik: Optional[str] = Field(default=None, min_length=8)
    alamat: Optional[str] = None
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    jumlah_anggota: Optional[int] = Field(default=None, ge=1)
    status_verifikasi: Optional[str] = None
    catatan_admin: Optional[str] = None


class KeluargaVerifikasi(BaseModel):
    status_verifikasi: str
    catatan_admin: Optional[str] = None