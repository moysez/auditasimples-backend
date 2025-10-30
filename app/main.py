from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.db import Base, engine
from app.routers import auth, uploads, dashboard, dictionary, clients, company

# ============================================================
# 🚀 CONFIGURAÇÃO INICIAL DO APP
# ============================================================

# Cria tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

# Logger global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("auditasimples")

# Instância principal
app = FastAPI(
    title="AuditaSimples API",
    description="API fiscal e tributária automatizada do AuditaSimples",
    version="1.0.0"
)

# ============================================================
# 🌐 CORS
# ============================================================
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ✅ HANDLER GLOBAL PARA OPTIONS (resolve erro 405)
# ============================================================
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """Responde a qualquer requisição OPTIONS para evitar erro 405."""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return Response(status_code=200, headers=headers)

# ============================================================
# 📦 REGISTRO DOS ROUTERS
# ============================================================
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(company.router, prefix="/api/company", tags=["Company"])

# ============================================================
# 🩺 HEALTH CHECK
# ============================================================
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AuditaSimples API funcionando corretamente"}

# ============================================================
# 🏁 LOG FINAL
# ============================================================
logger.info("✅ AuditaSimples API iniciada com sucesso e CORS ativo.")
logger.info("🌍 Domínios permitidos: %s", ", ".join(origins))
