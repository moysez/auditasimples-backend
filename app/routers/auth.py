from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.user import User
from ..services.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Usuário já existe")
    user = User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    return {"message": "Usuário criado com sucesso"}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
