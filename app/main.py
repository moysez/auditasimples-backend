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
    "https://auditasimples.io",   # domínio do frontend em produção
    "http://localhost:5500",      # opcional, útil se for testar localmente
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # ✅ Garante aceitação de POST, OPTIONS etc
    allow_headers=["*"],   # ✅ Garante que Authorization e Content-Type passem
    expose_headers=["*"],  # 👈 útil se precisar ler headers na resposta
    max_age=3600           # 👈 cacheia preflight, melhora performance
)

# -----------------------------
# 3. Banco de dados
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Rotas com prefixo /api
# -----------------------------
api_router = APIRouter(prefix="/api")

api_router.include_router(login_router)
api_router.include_router(clients.router)
api_router.include_router(uploads.router)
api_router.include_router(analyses.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)

@api_router.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

# Registra tudo no app principal
app.include_router(api_router)
