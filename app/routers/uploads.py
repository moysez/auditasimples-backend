from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

# 📁 Diretório onde os arquivos serão salvos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    client_id: str = Form(None)
):
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            f.write(await file.read())

        return JSONResponse({
            "filename": file.filename,
            "message": "Upload realizado com sucesso",
            "client_id": client_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
