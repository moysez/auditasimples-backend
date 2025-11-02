from datetime import datetime, timedelta
import hashlib
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Função para gerar hash da senha
def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

# Cria o token JWT
def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# Endpoint de login
@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or user.password_hash != _hash(data.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_token(user.username)
    return TokenResponse(access_token=token)

# Função para validar token e retornar usuário atual
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
