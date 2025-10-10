from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from ..db import get_session  # 👈 use get_session, não get_db (se no seu projeto o nome for assim)
from ..models.user import User
from ..services.auth import get_password_hash, verify_password, create_access_token

# ✅ prefixo único e claro
router = APIRouter(prefix="/auth", tags=["Auth"])

# 📌 Registrar novo usuário (admin no seu caso)
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

# 📌 Login
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
