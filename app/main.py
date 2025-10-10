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
# ❗ Inclua todos os domínios que podem chamar a API.
# É importante que seja EXATAMENTE igual ao "Origin" do navegador.
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",  # se for acessado com www
    "http://localhost:5500",         # ambiente local opcional
]

# ⚠️ Middleware CORS sempre ANTES das rotas
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
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

# 🔹 Health check
@api_router.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

# 🔹 Registrar rotas no app principal
app.include_router(api_router)
