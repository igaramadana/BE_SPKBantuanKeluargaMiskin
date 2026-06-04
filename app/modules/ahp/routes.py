from fastapi import APIRouter

from app.modules.ahp import service
from app.modules.ahp.schemas import AhpCalculateRequest


router = APIRouter()


@router.post("/calculate")
def calculate_ahp(payload: AhpCalculateRequest):
    return service.gas_hitung_ahp(payload)