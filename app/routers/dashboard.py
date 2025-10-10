from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..db import get_session
from ..services.storage import get_zip_bytes_from_db
from ..services.analysis import run_analysis_from_bytes

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    db: Session = Depends(get_session)
):
    try:
        zip_bytes = get_zip_bytes_from_db(upload_id, db)
        result = run_analysis_from_bytes(zip_bytes)

        return {
            "cards": {
                "documentos": result["documents"],
                "itens": result["items"],
                "valor_total": result["total_value_sum"],
                "economia_simulada": result["savings_simulated"],
                "periodo": f"{result['period_start']} - {result['period_end']}"
            },
            "erros_fiscais": {
                "monofasico_sem_ncm": result["monofasico_sem_ncm"],
                "monofasico_desc": result["monofasico_palavra_chave"],
                "monofasico_ia": result["monofasico_ia_detectado"],
                "st_corretos": result["st_cfop_csosn_corretos"],
                "st_incorretos": result["st_incorreta"]
            }

        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados do dashboard")
