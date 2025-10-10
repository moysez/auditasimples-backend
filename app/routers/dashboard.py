from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.upload import Upload
from ..models.report import Report
from ..services.analysis import run_analysis_from_bytes

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(company_id: int = Query(...), upload_id: int = Query(...), db: Session = Depends(get_db)):
    upload = db.query(Upload).filter_by(id=upload_id, company_id=company_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    result = run_analysis_from_bytes(upload.zip_data)
    report = Report(company_id=company_id, upload_id=upload.id, resultado=result)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "resultado": result}
