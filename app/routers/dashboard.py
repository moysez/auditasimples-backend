from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.analysis import run_analysis_for_upload

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/")
def get_dashboard(
    client_id: int = Query(..., description="ID do cliente"),
    upload_id: Optional[str] = Query(None, description="ID do upload (storage_key)")
):
    """
    Retorna os dados analíticos fiscais para exibição no dashboard.
    """
    try:
        if not upload_id:
            raise HTTPException(status_code=400, detail="upload_id obrigatório")

        # Chama a mesma função de análise que já está pronta
        result = run_analysis_for_upload(upload_id)
        return {"cards": {
            "documentos": result["documents"],
            "itens": result["items"],
            "valor_total": result["total_value_sum"],
            "economia_simulada": result["savings_simulated"],
            "periodo": f"{result['period_start']} - {result['period_end']}"
        },
        "erros_fiscais": {
            "monofasico_sem_ncm": result["monofasico_sem_ncm"],
            "monofasico_desc": result["monofasico_palavra_chave"],
            "st_corretos": result["st_cfop_csosn_corretos"],
            "st_incorretos": result["st_incorreta"]
        }}
    except Exception as e:
        print(f"❌ Erro interno no dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados do dashboard")
