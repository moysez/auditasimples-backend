from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os

from ..db import get_session
from ..models.uploads import Upload

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

# 📂 Diretório onde os arquivos ZIP/XML serão armazenados
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = Form(...),
    db: Session = Depends(get_session)
):
    try:
        # 🗂️ Salva arquivo físico
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # 🧾 Cria registro no banco
        upload = Upload(
            client_id=client_id,
            filename=file.filename,
            filepath=file_location
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)

        return JSONResponse({
            "id": upload.id,
            "filename": upload.filename,
            "client_id": upload.client_id,
            "message": "✅ Upload realizado com sucesso"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar upload: {e}")
