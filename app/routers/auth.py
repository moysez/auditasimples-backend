from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..db import get_session
from ..models.user import User
from ..services.auth import get_password_hash, verify_password, create_access_token
from .config import settings

router = APIRouter(
    prefix="/auth",   # 👈 prefixo padronizado
    tags=["Auth"]
)

# 📌 Registro de novo usuário (admin ou outros)
@router.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Usuário já existe")
    user = User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    return {"message": "Usuário criado com sucesso"}

# 📌 Login com verificação no banco
@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
