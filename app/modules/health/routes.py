from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def cek_api():
    return {
        "status": "Ok bro",
        "message": "API SPK aman guys."
    }