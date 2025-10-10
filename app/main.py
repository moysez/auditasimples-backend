from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text  # 👈 Import necessário para SELECT no SQLAlchemy 2.x

# 📦 Imports internos
from .config import settings
from .db import Base, engine, get_session
from .auth import login_router

# ⚠️ Caso você tenha movido as rotas para services, importe-as assim:
# from .services.clients import router as clients_router
# from .services.uploads import router as uploads_router
# from .services.analysis import router as analyses_router
# from .services.dashboard import router as dashboard_router

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

# Se você tiver outras rotas:
# api.include_router(clients_router)
# api.include_router(uploads_router)
# api.include_router(analyses_router)
# api.include_router(dashboard_router)

# -----------------------------
# 5. Health check simples
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

# -----------------------------
# 6. Health check do Banco (corrigido)
# -----------------------------
@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))  # 👈 Usando text() para SQLAlchemy 2.x
            return {"status": "ok", "result": [row[0] for row in result]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# -----------------------------
# 7. Registrar o roteador principal
# -----------------------------
app.include_router(api)
