from fastapi import HTTPException


def gas_hitung_ahp(payload):
    try:
        return {
            "message": "Endpoint AHP aktif. Logic perhitungan AHP bisa dilengkapi nanti.",
            "weights": [],
            "consistency_index": None,
            "consistency_ratio": None,
            "is_consistent": None,
            "data": payload.model_dump(),
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )