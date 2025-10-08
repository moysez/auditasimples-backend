import os, io, uuid
from fastapi import UploadFile
from ..config import settings

async def save_zip_and_return_key(file: UploadFile) -> str:
    key = f"uploads/{uuid.uuid4().hex}_{file.filename}"
    local_dir = settings.LOCAL_STORAGE_DIR
    os.makedirs(local_dir, exist_ok=True)
    dest = os.path.join(local_dir, key)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(await file.read())
    return key

def get_zip_bytes(key: str) -> bytes:
    path = os.path.join(settings.LOCAL_STORAGE_DIR, key)
    with open(path, "rb") as f:
        return f.read()
