from datetime import datetime, timedelta
import hashlib
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.config import settings  # usa a classe Settings do config.py

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)

# ============================================================
# 🔐 Funções auxiliares
# ============================================================

def _hash(pwd: str) -> str:
    """Gera hash SHA256 de uma senha."""
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

def create_token(sub: str) -> str:
    """Cria token JWT com expiração."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# ============================================================
# 🔑 LOGIN
# ============================================================

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_session)):
    """
    Autentica usuário (admin padrão: admin / 102030*)
    """
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if user.hashed_password != _hash(data.password):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token = create_token(user.username)
    return TokenResponse(access_token=token)

# ============================================================
# 👤 USUÁRIO ATUAL (para endpoints protegidos)
# ============================================================

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session),
) -> User:
    """
    Valida token JWT e retorna o usuário autenticado.
    """
    if not creds:
        raise HTTPException(status_code=401, detail="Não autenticado")

    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário inativo ou inexistente")

    return user
