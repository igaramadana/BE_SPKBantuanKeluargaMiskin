from fastapi import HTTPException
from app.modules.kriteria import repository

def gas_ambil_semua_kriteria():
    return repository.ambil_semua_kriteria()

def gas_bikin_kriteria(payload):
    if payload.jenis not in ["benefit", "cost"]:
        raise HTTPException(
            status_code=400,
            detail="Jenis kriteria harus 'benefit' atau 'cost'."
        )
    
    try:
        return repository.bikin_kriteria(payload)
    
    except Exception as error:
        raise HTTPException(
            status_code = 400,
            detail=str(error)
        )