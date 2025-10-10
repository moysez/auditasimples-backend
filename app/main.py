from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_session

# 🔐 Auth
from .auth import router as auth_router

# 📊 Rotas principais
from .routers import clients, company, uploads  # 👈 login removido aqui se não existir

app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

api = APIRouter(prefix="/api")

# 🔸 Se ainda não criou login, REMOVA esta linha
# api.include_router(login_router)

api.include_router(clients.router)
api.include_router(company.router)
api.include_router(uploads.router)
api.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {"status": "ok", "result": [row for row in result]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

app.include_router(api)
