from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.utils import verify_password, create_access_token

router = APIRouter()

# ============================================================
# 🔐 LOGIN DE USUÁRIO (email OU username)
# ============================================================
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica o usuário usando username ou email.
    Retorna um token JWT se as credenciais estiverem corretas.
    """

    # 1️⃣ Tenta encontrar por username
    user = db.query(User).filter(User.__dict__.get("username") == request.username).first() \
        if hasattr(User, "username") else None

    # 2️⃣ Se não encontrou e o model tem email, tenta por email
    if not user and hasattr(User, "email"):
        user = db.query(User).filter(User.email == request.username).first()

    # 3️⃣ Usuário não encontrado
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado."
        )

    # 4️⃣ Senha incorreta
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta."
        )

    # 5️⃣ Gera o token JWT
    token_data = {"sub": getattr(user, "username", getattr(user, "email", "unknown"))}
    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================
# 🩺 TESTE DE STATUS DO ENDPOINT (debug local)
# ============================================================
@router.get("/check")
def check_auth_api():
    return {"status": "ok", "message": "Rota /api/auth ativa e pronta para login"}
