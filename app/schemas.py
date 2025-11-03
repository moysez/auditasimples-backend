from pydantic import BaseModel

# ============================================================
# 📦 SCHEMAS DE LOGIN
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
