from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_session
from ..auth import get_current_user
from ..models import Upload, AnalysisJob, Report
from ..services.analysis import run_analysis_for_upload

router = APIRouter(prefix='/analyses', tags=['analyses'])

@router.post('/run')
def run_analysis(upload_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    up = db.query(Upload).get(upload_id)
    if not up:
        raise HTTPException(404, detail='Upload não encontrado')
    job = AnalysisJob(client_id=up.client_id, upload_id=up.id, status='processing')
    db.add(job); db.commit(); db.refresh(job)
    try:
        summary = run_analysis_for_upload(up.storage_key)
        job.status = 'done'
        job.summary = str(summary)
        db.add(job); db.commit()
        rep = Report(client_id=up.client_id, analysis_id=job.id, title='Resumo da Análise', findings=summary, totals={})
        db.add(rep); db.commit(); db.refresh(rep)
    except Exception as e:
        job.status = 'failed'; job.summary = str(e)
        db.add(job); db.commit()
        raise
    return {'job_id': job.id, 'status': job.status, 'summary': summary}
