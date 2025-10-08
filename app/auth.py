from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from .config import settings

login_router = APIRouter()
security = HTTPBearer()

class LoginPayload(BaseModel):
    username: str
    password: str

def create_token(username: str):
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(hours=12), "iat": datetime.utcnow()}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials if creds else None
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": payload["sub"]}

@login_router.post("/login")
def api_login(body: LoginPayload):
    if body.username == settings.ADMIN_USER and body.password == settings.ADMIN_PASS:
        return {"token": create_token(body.username)}
    raise HTTPException(status_code=401, detail="Credenciais inválidas")
