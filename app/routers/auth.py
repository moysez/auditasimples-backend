from fastapi import APIRouter, HTTPException
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["Auth"])

# ============================================================
# 🔐 LOGIN ÚNICO (admin fixo)
# ============================================================

ADMIN_USER = "admin"
ADMIN_PASS = "102030"

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    """Autenticação fixa sem banco de dados"""
    if data.username != ADMIN_USER or data.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    # Retorna token simbólico (apenas para compatibilidade)
    return TokenResponse(access_token="dummy-token", token_type="bearer")
