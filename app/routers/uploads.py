from fastapi import APIRouter, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from ..db import get_session
from ..services.storage import save_zip_and_return_id

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post("/")
async def upload_file(
    client_id: int = Form(...),
    file: UploadFile = None,
    db: Session = Depends(get_session)
):
    upload_id = await save_zip_and_return_id(file, client_id, db)
    return {"message": "Upload salvo com sucesso", "upload_id": upload_id}
