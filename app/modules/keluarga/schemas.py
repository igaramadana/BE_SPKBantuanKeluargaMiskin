from typing import Any, List, Optional

from pydantic import BaseModel


class PenilaianManualItem(BaseModel):
    kode_kriteria: str
    nilai_awal: float


class KeluargaCreateRequest(BaseModel):
    nama_kepala_keluarga: str
    nik: str
    alamat: Optional[str] = None
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    jumlah_anggota: Optional[int] = None
    penilaian: Optional[List[PenilaianManualItem]] = None


class KeluargaUpdateRequest(BaseModel):
    nama_kepala_keluarga: Optional[str] = None
    nik: Optional[str] = None
    alamat: Optional[str] = None
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    jumlah_anggota: Optional[int] = None
    status_verifikasi: Optional[str] = None
    catatan_admin: Optional[str] = None
    penilaian: Optional[List[PenilaianManualItem]] = None


class KeluargaVerifikasiRequest(BaseModel):
    status_verifikasi: str
    catatan_admin: Optional[str] = None


class KeluargaResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    nama_kepala_keluarga: str
    nik: str
    alamat: Optional[str] = None
    kelurahan: Optional[str] = None
    dusun: Optional[str] = None
    jumlah_anggota: Optional[int] = None
    status_verifikasi: str
    catatan_admin: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Any
    updated_at: Optional[Any] = None