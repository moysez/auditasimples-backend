# services/storage.py
async def save_zip_in_db(file) -> bytes:
    """
    Lê e retorna o conteúdo binário do arquivo ZIP enviado.
    """
    return await file.read()
