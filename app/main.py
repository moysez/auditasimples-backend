from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.db import Base, engine
from app.routers import auth, uploads, dashboard, dictionary, clients, company

# ============================================================
# 🚀 CONFIGURAÇÃO INICIAL DO APP
# ============================================================

# Garante as tabelas
Base.metadata.create_all(bind=engine)

# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("auditassimples")

app = FastAPI(
    title="AuditaSimples API",
    description="API fiscal e tributária do AuditaSimples",
    version="1.0.0",
)

# ============================================================
# 🌐 CORS (somente os domínios que você usa)
# ============================================================
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# 📦 ROTAS
# ============================================================
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(uploads.router,    prefix="/api/uploads",    tags=["Uploads"])
app.include_router(dashboard.router,  prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])
app.include_router(clients.router,    prefix="/api/clients",    tags=["Clients"])
app.include_router(company.router,    prefix="/api/company",    tags=["Company"])

# ============================================================
# 🩺 HEALTH CHECK
# ============================================================
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AuditaSimples API funcionando corretamente"}

logger.info("✅ AuditaSimples API iniciada com sucesso.")
