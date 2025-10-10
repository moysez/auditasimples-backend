from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# 📦 Importações internas
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
# ⚠️ Domínios que podem chamar a API — devem bater exatamente com o Origin do navegador
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",  # se for acessado com www
    "http://localhost:5500",         # ambiente local opcional
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # permite Authorization, Content-Type, etc.
    expose_headers=["*"],
    max_age=3600           # cache do preflight
)

# -----------------------------
# 3. Inicialização do banco de dados
# -----------------------------
# 🔹 Cria as tabelas automaticamente (caso não existam)
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Registro das rotas
# -----------------------------
api_router = APIRouter(prefix="/api")

# 📌 Rotas de autenticação
api_router.include_router(login_router)

# 📌 Rotas principais
api_router.include_router(clients.router)
api_router.include_router(uploads.router)
api_router.include_router(analyses.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)

# -----------------------------
# 5. Health check (para monitoramento)
# -----------------------------
@api_router.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

# -----------------------------
# 6. Registro do roteador principal
# -----------------------------
app.include_router(api_router)
