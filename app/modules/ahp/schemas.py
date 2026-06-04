from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AhpComparisonItem(BaseModel):
    kriteria_1_id: str
    kriteria_2_id: str
    nilai: float = Field(..., gt=0)


class AhpCalculateRequest(BaseModel):
    perbandingan: List[AhpComparisonItem]
    simpan_bobot: bool = True


class AhpWeightResult(BaseModel):
    kriteria_id: str
    bobot: float


class AhpCalculateResponse(BaseModel):
    message: str
    weights: List[AhpWeightResult]
    consistency_index: Optional[float] = None
    consistency_ratio: Optional[float] = None
    is_consistent: Optional[bool] = None
    data: Optional[Any] = None