from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importações dos módulos internos
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
    "https://auditasimples.io",
    "https://www.auditasimples.io",  # 👈 Adicione o www se o front usar
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # 👈 importante para OPTIONS
    allow_headers=["*"],   # 👈 libera Content-Type, Authorization etc.
)

# -----------------------------
# 3. Banco de dados
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Rotas
# -----------------------------
app.include_router(login_router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(analyses.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# -----------------------------
# 5. Health check
# -----------------------------
@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}
