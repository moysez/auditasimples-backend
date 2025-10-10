import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ..models import Upload

# 📦 Salva ZIP no banco
async def save_zip_and_return_id(file: UploadFile, client_id: int, db: Session) -> int:
    file_bytes = await file.read()
    new_upload = Upload(
        client_id=client_id,
        filename=file.filename,
        file_data=file_bytes
    )
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    return new_upload.id

# 📥 Recupera ZIP do banco
def get_zip_bytes_from_db(upload_id: int, db: Session) -> bytes:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise FileNotFoundError(f"Upload ID {upload_id} não encontrado")
    return upload.file_data
