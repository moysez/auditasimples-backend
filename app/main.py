from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Importações internas
from .config import settings
from .db import Base, engine
from .auth import login_router
from .routers import clients, uploads, analyses, reports, dashboard

# -----------------------------
# 1. Criação da aplicação
# -----------------------------
app = FastAPI(
    title="AuditaSimples API",
    version="0.2.0"
)

# -----------------------------
# 2. Configuração de CORS
# -----------------------------
origins = [
    "https://auditasimples.io",  # domínio do frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 3. Banco de dados
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Rotas com prefixo /api
# -----------------------------
api_router = APIRouter(prefix="/api")

# Inclui todas as rotas dentro do /api
api_router.include_router(login_router)
api_router.include_router(clients.router)
api_router.include_router(uploads.router)
api_router.include_router(analyses.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)

# Health check padronizado
@api_router.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

# Registra tudo no app principal
app.include_router(api_router)
