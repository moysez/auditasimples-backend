from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os, traceback

from ..db import get_session
from ..models.upload import Upload

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

# 📁 Diretório de armazenamento
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===============================
# 📤 UPLOAD DE ARQUIVO ZIP
# ===============================
@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = Form(...),
    db: Session = Depends(get_session)
):
    try:
        # 🗂️ Salvar arquivo físico no diretório
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            f.write(await file.read())

        print(f"✅ Arquivo salvo em: {file_location}")
        print(f"📎 client_id recebido: {client_id}")

        # 📝 Salvar metadados no banco
        upload_record = Upload(
            client_id=client_id,
            filename=file.filename,
            filepath=file_location
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        print(f"📦 Upload salvo no banco com ID: {upload_record.id}")

        return JSONResponse({
            "id": upload_record.id,
            "filename": upload_record.filename,
            "client_id": upload_record.client_id
        })

    except Exception as e:
        print("❌ Erro ao salvar no banco:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# 📋 LISTAR UPLOADS POR EMPRESA
# ===============================
@router.get("/list")
def list_uploads(
    client_id: int = Query(...),
    db: Session = Depends(get_session)
):
    try:
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
                "created_at": u.uploaded_at.isoformat() if u.uploaded_at else None
            }
            for u in uploads
        ]

    except Exception as e:
        print("❌ Erro ao listar uploads:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
    # 👇 Função que substitui o storage.py
    def get_zip_bytes_from_db(upload_id: int, db: Session) -> bytes:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload or not os.path.exists(upload.filepath):
            raise FileNotFoundError("Arquivo não encontrado")
        with open(upload.filepath, "rb") as f:
            return f.read()
