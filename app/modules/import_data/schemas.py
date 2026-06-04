from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ImportBatchResponse(BaseModel):
    id: str
    nama_file: str
    jumlah_baris: int
    jumlah_valid: int
    jumlah_error: int
    uploaded_by: Optional[str] = None
    created_at: Any


class ImportPreviewResponse(BaseModel):
    filename: str
    columns: List[str]
    total_rows: int
    preview: List[Dict[str, Any]]
    missing_required_columns: List[str]


class SaveRawImportResponse(BaseModel):
    message: str
    batch: Dict[str, Any]
    jumlah_valid: int
    jumlah_error: int


class MappingImportRequest(BaseModel):
    import_batch_id: str

    kolom_nama_kepala_keluarga: Optional[str] = None
    kolom_nik: Optional[str] = None
    kolom_alamat: Optional[str] = None
    kolom_kelurahan: str
    kolom_dusun: str
    kolom_jumlah_anggota: str

    kolom_skor_c1: Optional[str] = "skor_C1_kondisi_rumah"
    kolom_skor_c2: Optional[str] = "skor_C2_jumlah_tanggungan"
    kolom_skor_c3: Optional[str] = "skor_C3_pekerjaan_kepala_keluarga"
    kolom_skor_c4: Optional[str] = "skor_C4_kepemilikan_aset_cost"
    kolom_skor_c5: Optional[str] = "skor_C5_fasilitas_dasar"
    kolom_skor_c6: Optional[str] = "skor_C6_pendidikan_kepala_keluarga"


class MappingImportResponse(BaseModel):
    message: str
    total_diproses: int
    total_berhasil: int
    total_gagal: int
    total_penilaian_berhasil: int
    total_penilaian_gagal: int
    errors: List[str]