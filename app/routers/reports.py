from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.report import Report

router = APIRouter(
    tags=["Reports"]
)

@router.get("/{company_id}")
def list_reports(company_id: int, db: Session = Depends(get_db)):
    return db.query(Report).filter_by(company_id=company_id).order_by(Report.created_at.desc()).all()
