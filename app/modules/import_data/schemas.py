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


class AutoGeneratePenilaianRequest(BaseModel):
    import_batch_id: str
    preview_only: bool = True
    limit_preview: int = 50


class AutoGeneratePenilaianResponse(BaseModel):
    message: str
    import_batch_id: str
    preview_only: bool
    total_raw: int
    total_grouped: int
    total_keluarga_berhasil: int
    total_penilaian_berhasil: int
    total_gagal: int
    preview: List[Dict[str, Any]]
    errors: List[str]


# Backward compatibility untuk endpoint lama.
class MappingImportRequest(BaseModel):
    import_batch_id: str

    kolom_nama_kepala_keluarga: Optional[str] = None
    kolom_nik: Optional[str] = None
    kolom_alamat: Optional[str] = None
    kolom_kelurahan: str = "kelurahan"
    kolom_dusun: str = "dusun"
    kolom_jumlah_anggota: str = "jml_anggota_keluarga"

    kolom_skor_c1: Optional[str] = None
    kolom_skor_c2: Optional[str] = None
    kolom_skor_c3: Optional[str] = None
    kolom_skor_c4: Optional[str] = None
    kolom_skor_c5: Optional[str] = None
    kolom_skor_c6: Optional[str] = None


class MappingImportResponse(BaseModel):
    message: str
    total_diproses: int
    total_berhasil: int
    total_gagal: int
    total_penilaian_berhasil: int
    total_penilaian_gagal: int
    errors: List[str]