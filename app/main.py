from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.db import Base, engine
from app.routers import auth, uploads, dashboard, dictionary, clients, company

# ============================================================
# 🚀 CONFIGURAÇÃO INICIAL DO APP
# ============================================================

# Cria tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

# Logger global configurado para exibir logs no Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("auditassimples")

# Inicializa o app
app = FastAPI(
    title="AuditaSimples API",
    description="API fiscal e tributária automatizada do AuditaSimples",
    version="1.0.0"
)

# ============================================================
# 🌐 CONFIGURAÇÃO DE CORS
# ============================================================
# Domínios autorizados
origins = [
    "https://auditassimples.io",
    "https://www.auditassimples.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

# Middleware de CORS com fallback (para evitar bloqueio no navegador)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Domínios específicos
    allow_origin_regex=".*",        # Garante compatibilidade com subdomínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """
    Endpoint de verificação do status do serviço.
    Usado pelo Render e testes locais.
    """
    return {"status": "ok", "message": "AuditaSimples API funcionando corretamente"}

# ============================================================
# 🏁 LOG DE INICIALIZAÇÃO
# ============================================================
logger.info("✅ AuditaSimples API iniciada com sucesso e CORS liberado.")
logger.info("🌍 Domínios permitidos: %s", ", ".join(origins))
