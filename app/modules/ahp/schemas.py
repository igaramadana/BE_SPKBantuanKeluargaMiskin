from pydantic import BaseModel
from typing import List

class AhpRequest(BaseModel):
    kriteria_ids: List[str]
    matrix: List[List[float]]