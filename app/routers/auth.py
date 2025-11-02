from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import jwt

from app.db import get_session
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.config import settings  # usa a classe Settings do config.py

router = APIRouter()

def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()

def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if user.hashed_password != _hash(data.password):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    token = create_token(user.username)
    return TokenResponse(access_token=token)
