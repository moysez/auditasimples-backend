from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 📦 Imports internos
from .config import settings
from .db import Base, engine, get_session
from .auth import login_router
from .routers import clients, uploads, analyses, reports, dashboard

# -----------------------------
# 1. Criação da aplicação
# -----------------------------
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# -----------------------------
# 2. CORS
# -----------------------------
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5500"  # opcional para ambiente local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 3. Criar tabelas no banco (PostgreSQL)
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Rotas da API
# -----------------------------
api = APIRouter(prefix="/api")
api.include_router(login_router)
api.include_router(clients.router)
api.include_router(uploads.router)
api.include_router(analyses.router)
api.include_router(reports.router)
api.include_router(dashboard.router)

# -----------------------------
# 5. Health check simples
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

# -----------------------------
# 6. Health check do Banco
# -----------------------------
@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {"status": "ok", "result": [row for row in result]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# -----------------------------
# 7. Registrar o roteador principal
# -----------------------------
app.include_router(api)
