from datetime import datetime, timedelta
import hashlib
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User  # ⚠️ aqui é o User do app.models
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["Auth"])
security = HTTPBearer(auto_error=False)


# ============================================================
# 🔐 UTILITÁRIOS
# ============================================================

def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=60)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


# ============================================================
# 🧠 LOGIN
# ============================================================

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_session)):
    # ⚠️ Aqui garantimos que User vem do models
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    if user.hashed_password != _hash(data.password):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    token = create_token(user.username)
    return TokenResponse(access_token=token)


# ============================================================
# 👤 USUÁRIO ATUAL
# ============================================================

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Não autenticado")

    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário inativo")

    return user
