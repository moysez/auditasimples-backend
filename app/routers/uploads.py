import os
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from ..db import get_session as get_db
from app.models import Upload
from app.services.analysis import run_analysis_from_bytes

router = APIRouter(tags=["Uploads"])
IS_RENDER = os.getenv("ENV") == "render"

@router.post("/path")
def register_local_path(client_id: int = Form(...), filename: str = Form(...), filepath: str = Form(...), db: Session = Depends(get_db)):
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Caminho local não encontrado.")
    new_upload = Upload(client_id=client_id, filename=filename, filepath=filepath)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    return {"message": "Caminho salvo com sucesso", "upload_id": new_upload.id}

@router.get("/list", response_model=List[dict])
def list_files(client_id: int, db: Session = Depends(get_db)):
    uploads = db.query(Upload).filter(Upload.client_id == client_id).order_by(Upload.uploaded_at.desc()).all()
    return [{"id": u.id, "filename": u.filename, "uploaded_at": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"), "path": u.filepath} for u in uploads]

@router.get("/analyze/{upload_id}")
def analyze_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    if IS_RENDER:
        raise HTTPException(status_code=400, detail="Execução local não disponível em produção (Render).")

    if not os.path.exists(upload.filepath):
        raise HTTPException(status_code=404, detail=f"Arquivo local não encontrado: {upload.filepath}")

    try:
        with open(upload.filepath, "rb") as f:
            zip_bytes = f.read()
        result = run_analysis_from_bytes(zip_bytes)
        return {"status": "ok", "summary": result.get("tax_summary"), "totals": result["tax_summary"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
