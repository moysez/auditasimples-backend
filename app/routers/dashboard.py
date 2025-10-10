from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_session
from ..auth import get_current_user
from ..models import Upload
from ..services.analysis import run_analysis_for_upload

router = APIRouter(prefix='/dashboard', tags=['dashboard'])

@router.get('')
def get_dashboard(client_id: int, upload_id: Optional[int] = None,
                  db: Session = Depends(get_session), user=Depends(get_current_user)):
    qry = db.query(Upload).filter(Upload.client_id == client_id).order_by(Upload.id.desc())
    up = db.query(Upload).get(upload_id) if upload_id else qry.first()
    if not up:
        raise HTTPException(404, detail='Nenhum upload encontrado para o cliente.')
    summary = run_analysis_for_upload(up.storage_key)
    return {
        'client_id': client_id,
        'upload_id': up.id,
        'summary': summary,
        'cards': {
            'documentos': summary['documents'],
            'itens': summary['items'],
            'valor_total': summary['total_value_sum'],
            'periodo': f"{summary.get('period_start','?')} a {summary.get('period_end','?')}",
            'economia_simulada': summary['savings_simulated'],
        },
        'erros_fiscais': {
            'monofasico_sem_ncm': summary['monofasico_sem_ncm'],
            'monofasico_desc': summary['monofasico_palavra_chave'],
            'st_corretos': summary['st_cfop_csosn_corretos'],
            'st_incorretos': summary['st_incorreta'],
        },
    }
