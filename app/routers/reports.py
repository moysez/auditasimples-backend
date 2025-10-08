from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_session
from ..models import Report
from ..schemas import ReportOut
from ..auth import get_current_user
from typing import List

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_session), user=Depends(get_current_user)):
    return db.query(Report).order_by(Report.id.desc()).all()

@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    r = db.query(Report).get(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return r
