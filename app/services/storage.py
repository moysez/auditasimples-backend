import os
import uuid
from fastapi import UploadFile
from ..config import settings

# ============================
# 📁 Salvar arquivo ZIP no storage local
# ============================
async def save_zip_and_return_key(file: UploadFile) -> str:
    """
    Salva um arquivo ZIP no diretório local e retorna uma chave única (storage key).
    """
    key = f"uploads/{uuid.uuid4().hex}_{file.filename}"
    base_dir = settings.LOCAL_STORAGE_DIR

    # Garante que a pasta existe
    os.makedirs(os.path.join(base_dir, "uploads"), exist_ok=True)

    # Caminho de destino
    dest = os.path.join(base_dir, key)
    with open(dest, "wb") as f:
        f.write(await file.read())

    return key

# ============================
# 📍 Retornar caminho completo do arquivo ZIP salvo
# ============================
def get_zip_path(key: str) -> str:
    """
    Retorna o caminho absoluto do arquivo ZIP salvo.
    """
    return os.path.join(settings.LOCAL_STORAGE_DIR, key)

# ============================
# 📦 Ler arquivo ZIP em bytes (caso precise processar depois)
# ============================
def get_zip_bytes(key: str) -> bytes:
    """
    Lê o arquivo ZIP salvo e retorna os bytes.
    """
    file_path = get_zip_path(key)
    with open(file_path, "rb") as f:
        return f.read()
