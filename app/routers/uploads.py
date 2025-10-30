from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import os

from app.db import get_session
from app.models import Upload
from app.services.analysis import run_analysis_from_bytes  # mantém seu analisador original

router = APIRouter()

# ============================================================
# 🆕 Registrar caminho local (NÃO faz upload)
# ============================================================
@router.post("/path")
def register_local_path(
    client_id: int = Form(...),
    filename: str = Form(...),
    filepath: str = Form(...),
    db: Session = Depends(get_session)
):
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Caminho local não encontrado.")

    new_upload = Upload(client_id=client_id, filename=filename, filepath=filepath)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    return {"message": "Caminho salvo com sucesso", "upload_id": new_upload.id}

# ============================================================
# 📋 Listar arquivos registrados por cliente
# ============================================================
@router.get("/list", response_model=List[dict])
def list_files(client_id: int, db: Session = Depends(get_session)):
    uploads = (
        db.query(Upload)
        .filter(Upload.client_id == client_id)
        .order_by(Upload.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": u.id,
            "filename": u.filename,
            "uploaded_at": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "path": u.filepath,
        }
        for u in uploads
    ]

# ============================================================
# 🔍 Rodar análise a partir do caminho local
# ============================================================
@router.get("/analyze/{upload_id}")
def analyze_upload(upload_id: int, db: Session = Depends(get_session)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    try:
        with open(upload.filepath, "rb") as f:
            zip_bytes = f.read()
        result = run_analysis_from_bytes(zip_bytes)
        return {"status": "ok", "summary": result.get("tax_summary"), "totals": result.get("tax_summary")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
