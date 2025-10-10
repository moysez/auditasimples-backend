from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.upload import Upload

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post("/")
async def upload_file(company_id: int = Form(...), file: UploadFile = None, db: Session = Depends(get_db)):
    if not file:
        raise HTTPException(status_code=400, detail="Arquivo não enviado")
    zip_bytes = await file.read()
    upload = Upload(company_id=company_id, original_name=file.filename, zip_data=zip_bytes)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return {"upload_id": upload.id, "filename": upload.original_name}
