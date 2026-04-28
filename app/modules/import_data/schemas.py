from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class MappingKolomRequest(BaseModel):
    import_batch_id: str
    kolom_nama_kepala_keluarga: Optional[str] = None
    kolom_nik: Optional[str] = None
    kolom_alamat: Optional[str] = None
    kolom_kelurahan: str
    kolom_dusun: str
    kolom_jumlah_anggota: str


class ImportBatchResponse(BaseModel):
    id: str
    nama_file: str
    jumlah_baris: int
    jumlah_valid: int
    jumlah_error: int


class ImportRawItem(BaseModel):
    id: str
    import_batch_id: str
    raw_json: Dict[str, Any]
    status_validasi: str
    error_message: Optional[str] = None


class ValidasiImportResponse(BaseModel):
    total_rows: int
    valid_rows: int
    error_rows: int
    errors: List[str]