from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Routers principais
from app.routers import auth, clients, uploads, dashboard, dictionary

# Banco de dados
from app.db import engine, Base

# =========================================
# 🚀 Configuração inicial da aplicação
# =========================================
app = FastAPI(
    title="AuditaSimples API",
    description="Backend principal para análise fiscal e auditoria do Simples Nacional",
    version="1.0.0",
)

# Criação automática das tabelas (se ainda não existirem)
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

# =========================================
# 🌐 CORS — liberar domínios autorizados
# =========================================
origins = [
    "https://auditassimples.io",
    "https://www.auditassimples.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 🔥 exato (não use "*")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# 🧭 Configuração de logging
# =========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("auditassimples")

# =========================================
# 🔌 Registro das rotas
# =========================================
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])

logger.info("🟢 Rotas registradas com sucesso:")
for r in app.routes:
    if hasattr(r, "path"):
        logger.info(f"   - {r.path}")

logger.info("✅ FASTAPI inicializado com CORS habilitado para:")
for origin in origins:
    logger.info(f"   - {origin}")

# =========================================
# 🔍 Healthcheck simples
# =========================================
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AuditaSimples API funcionando corretamente."}
