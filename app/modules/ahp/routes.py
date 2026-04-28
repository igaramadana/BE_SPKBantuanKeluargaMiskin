from fastapi import APIRouter, HTTPException
from app.modules.ahp.schemas import AhpRequest
from app.modules.ahp.service import hitung_ahp

router = APIRouter()

@router.post("/calcuate")
def gas_hitung_ahp(payload: AhpRequest):
    try:
        return hitung_ahp(payload.matrix)
    
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )