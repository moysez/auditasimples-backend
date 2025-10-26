from fastapi import APIRouter, HTTPException, Depends, Form, status
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from ..db import get_session
from ..models.user import User
from ..services.auth import get_password_hash, verify_password, create_access_token
from ..config import settings

# ✅ APENAS UM ROUTER
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# 📦 Modelo opcional
class LoginPayload(BaseModel):
    username: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# 🧑‍💻 Login com usuário fixo (admin)
@router.post("/login")
def login_admin(username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USER and password == settings.ADMIN_PASS:
        token = create_access_token({"sub": username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciais inválidas")

# 🧑‍💻 Login no banco de dados
@router.post("/login-db")
def login_db(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# 🧾 Registro de usuário
@router.post("/register")
def register_user(
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

# 🔐 Validar token recebido
def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou ausente"
        )
    return {"token": token}
