from fastapi import APIRouter, HTTPException, Form
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from .config import settings

# 📌 Cria um roteador único padronizado
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# 📦 Modelo para payload de login (opcional se usar Form)
class LoginPayload(BaseModel):
    username: str
    password: str

# 🔐 Função para gerar token JWT
def create_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=12),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# 🚪 Endpoint de Login
@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    # ⚠️ Aqui você pode trocar por consulta ao banco no futuro
    if username == settings.ADMIN_USER and password == settings.ADMIN_PASS:
        token = create_token(username)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciais inválidas")

# (Opcional) Endpoint de registro — só se for necessário no futuro
# @router.post("/register")
# def register(...):
#     ...
