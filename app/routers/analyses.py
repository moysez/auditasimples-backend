from fastapi import APIRouter, HTTPException
from typing import Dict
from ..services.analysis import run_analysis_for_upload

# 👇 Cria o objeto de rota exigido pelo main.py
router = APIRouter(
    prefix="/analyses",
    tags=["Analyses"]
)

@router.get("/{storage_key}", response_model=Dict)
def analyze_uploaded_file(storage_key: str):
    """
    Rota para rodar a análise fiscal sobre um arquivo ZIP já enviado.
    O storage_key deve ser o nome do arquivo salvo no storage.
    """
    try:
        result = run_analysis_for_upload(storage_key)
        return result
    except Exception as e:
        print(f"❌ Erro ao processar análise: {e}")
        raise HTTPException(status_code=400, detail="Falha ao processar o arquivo para análise")
