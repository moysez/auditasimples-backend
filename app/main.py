from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_session
from .auth import login_router
from .routers import clients, company

app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# ✅ Lista de origens permitidas
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500"  # para desenvolvimento local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Cria tabelas
Base.metadata.create_all(bind=engine)

# 📌 Rotas
api = APIRouter(prefix="/api")
api.include_router(login_router)
api.include_router(clients.router)
api.include_router(company.router)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        return {"status": "ok", "result": [row for row in result]}

app.include_router(api)
