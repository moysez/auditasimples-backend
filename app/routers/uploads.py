from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os, traceback

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

# ✅ No Render use /tmp (persistente na execução)
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    client_id: str = Form(...)
):
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)

        # 🔸 Grava o arquivo no servidor temporário
        with open(file_location, "wb") as f:
            f.write(await file.read())

        print(f"✅ Arquivo salvo em: {file_location}")
        print(f"📎 client_id recebido: {client_id}")

        return JSONResponse({
            "filename": file.filename,
            "client_id": client_id,
            "path": file_location
        })

    except Exception as e:
        # 🛑 Log detalhado do erro
        print("❌ Erro no upload:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")
