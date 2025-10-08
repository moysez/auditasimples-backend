from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_session
from ..models import AnalysisJob, Upload
from ..schemas import AnalysisOut
from ..auth import get_current_user
from ..services.analysis import run_analysis_for_upload
from typing import List

router = APIRouter(prefix="/analyses", tags=["analyses"])

@router.post("/{upload_id}", response_model=AnalysisOut)
def analyze_upload(upload_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    up = db.query(Upload).get(upload_id)
    if not up:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    job = AnalysisJob(client_id=up.client_id, upload_id=up.id, status="running")
    db.add(job); db.commit(); db.refresh(job)

    try:
        run_analysis_for_upload(db, upload=up, job=job)
        job.status = "done"
        job.summary = f"Upload {up.id} analisado"
        db.commit(); db.refresh(job)
    except Exception as e:
        job.status = "error"
        job.summary = str(e)
        db.commit(); db.refresh(job)
        raise

    return job

@router.get("/", response_model=List[AnalysisOut])
def list_analyses(db: Session = Depends(get_session), user=Depends(get_current_user)):
    return db.query(AnalysisJob).order_by(AnalysisJob.id.desc()).all()
