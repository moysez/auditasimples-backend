from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..db import get_session
from ..models import Upload, Client
from ..schemas import UploadOut
from ..auth import get_current_user
from ..services.storage import save_zip_in_db
from typing import List

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("/", response_model=UploadOut)
async def create_upload(
    client_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    file_data = await save_zip_in_db(file)

    up = Upload(client_id=client_id, filename=file.filename, file_data=file_data)
    db.add(up)
    db.commit()
    db.refresh(up)
    return up

@router.get("/", response_model=List[UploadOut])
def list_uploads(
    db: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    return db.query(Upload).order_by(Upload.id.desc()).all()
