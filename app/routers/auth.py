import os
import logging
from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from ..db import get_session
from app.models import User

# ------------------------------------------------------------
# ⚙️ Configuração geral
# ------------------------------------------------------------
router = APIRouter(tags=["Autenticação"])

logger = logging.getLogger("auditassimples.auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "chave-secreta-supersegura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 240

IS_RENDER = os.getenv("ENV", "local").lower() == "render"


# ------------------------------------------------------------
# 🔐 Funções auxiliares
# ------------------------------------------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------------------------------------------
# 🧾 Login de usuário
# ------------------------------------------------------------
@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_session)):
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Senha incorreta")

        token = create_access_token({"sub": username})
        logger.info(f"✅ Login bem-sucedido: {username}")

        return JSONResponse(content={
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username},
            "environment": "Render" if IS_RENDER else "Local"
        })

    except Exception as e:
        logger.exception("Erro inesperado no login")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------------------------------------------------
# 👤 Criação de usuário (para testes locais)
# ------------------------------------------------------------
@router.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_session)):
    """Endpoint opcional — útil apenas em ambiente local para criar usuários."""
    if IS_RENDER:
        raise HTTPException(status_code=403, detail="Criação de usuários desabilitada no ambiente de produção.")

    from app.models import User

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Usuário já existe")

    hashed_password = pwd_context.hash(password)
    user = User(username=username, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"👤 Usuário criado: {username}")
    return {"message": "Usuário criado com sucesso", "user_id": user.id}
