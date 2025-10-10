from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os, traceback

from ..db import get_session
from ..models.upload import Upload

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = Form(...),
    db: Session = Depends(get_session)
):
    try:
        # 🗂️ Salvar arquivo físico
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
