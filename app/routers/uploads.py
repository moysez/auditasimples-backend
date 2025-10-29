from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import io

from ..db import get_session as get_db
from app.models import Upload
from app.services.analysis import run_analysis_from_bytes  # <- seu motor principal de auditoria

router = APIRouter(prefix="/uploads", tags=["Uploads"])


# ============================================================
# 🔼 1. UPLOAD de arquivo ZIP/XML — salva BINÁRIO no banco
# ============================================================
@router.post("/")
async def upload_file(
    client_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Lê o arquivo em blocos de 4 MB (para evitar SSL timeout)
        CHUNK_SIZE = 4 * 1024 * 1024
        binary_data = b""
        while chunk := await file.read(CHUNK_SIZE):
            binary_data += chunk

        if not binary_data:
            raise HTTPException(status_code=400, detail="Arquivo vazio ou inválido")

        new_upload = Upload(
            client_id=client_id,
            filename=file.filename,
            filepath=binary_data  # coluna BYTEA
        )
        db.add(new_upload)
        db.commit()
        db.refresh(new_upload)

        return {
            "status": "ok",
            "id": new_upload.id,
            "filename": new_upload.filename,
            "size_bytes": len(binary_data)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")


# ============================================================
# 📂 2. LISTAR arquivos enviados por cliente
# ============================================================
@router.get("/list", response_model=List[dict])
def list_files(client_id: int, db: Session = Depends(get_db)):
    uploads = db.query(Upload).filter(Upload.client_id == client_id).order_by(Upload.uploaded_at.desc()).all()
    return [
        {
            "id": u.id,
            "filename": u.filename,
            "uploaded_at": u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "size_kb": round(len(u.filepath or b"") / 1024, 2)
        }
        for u in uploads
    ]


# ============================================================
# 🔍 3. RODAR ANÁLISE diretamente de um upload salvo
# ============================================================
@router.get("/analyze/{upload_id}")
def analyze_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    try:
        zip_bytes = bytes(upload.filepath)
        result = run_analysis_from_bytes(zip_bytes)
        return {
            "status": "ok",
            "summary": result.get("tax_summary"),
            "totals": {
                "faturamento": result["tax_summary"].get("faturamento", 0),
                "receita_excluida": result["tax_summary"].get("receita_excluida", 0),
                "imposto_corrigido": result["tax_summary"].get("imposto_corrigido", 0),
                "economia_estimada": result["tax_summary"].get("economia_estimada", 0),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {e}")


# ============================================================
# ⬇️ 4. DOWNLOAD (retorna o ZIP original)
# ============================================================
from fastapi.responses import StreamingResponse

@router.get("/download/{upload_id}")
def download_file(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    file_stream = io.BytesIO(upload.filepath)
    headers = {
        "Content-Disposition": f"attachment; filename={upload.filename}"
    }
    return StreamingResponse(file_stream, headers=headers, media_type="application/zip")
