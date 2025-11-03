from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["Auth"])
security = HTTPBearer(auto_error=False)

# ============================================================
# 🔐 USUÁRIO FIXO (SEM BANCO)
# ============================================================

HARDCODED_USERNAME = "admin"
HARDCODED_PASSWORD = "102030"  # <- senha fixa

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# 🔐 UTILITÁRIO PARA CRIAR TOKEN
# ============================================================

def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


# ============================================================
# 🧠 LOGIN (sem banco, só usuário fixo)
# ============================================================

@router.post("/login", response_model=TokenResponse)
def login(
    username: str = Form(...),
    password: str = Form(...),
):
    """
    Recebe username e password via formulário (FormData)
    e valida contra o usuário fixo admin / 102030.
    """

    if username != HARDCODED_USERNAME:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if password != HARDCODED_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha incorreta")

    token = create_token(username)
    return TokenResponse(access_token=token)


# ============================================================
# 👤 OBTÉM USUÁRIO ATUAL A PARTIR DO TOKEN
# (caso você queira reutilizar nas outras rotas futuramente)
# ============================================================

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Não autenticado")

    try:
        payload = jwt.decode(
            creds.credentials,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    username = payload.get("sub")
    if username != HARDCODED_USERNAME:
        raise HTTPException(status_code=401, detail="Usuário inválido")

    return username
