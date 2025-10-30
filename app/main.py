import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db import Base, engine
Base.metadata.create_all(bind=engine)

# Rotas internas
from app.routers import clients, company, uploads, dashboard, dictionary, auth

# Configurações de log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("auditassimples")

# ============================================================
# 🏗️ Inicialização do app
# ============================================================
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0",
    description="Backend para análise e auditoria fiscal do Simples Nacional"
)

# ============================================================
# 🌐 CORS
# ============================================================
IS_RENDER = os.getenv("ENV", "local").lower() == "render"

if IS_RENDER:
    origins = [
        "https://auditassimples.io",
        "https://www.auditassimples.io"
    ]
else:
    origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ FASTAPI inicializado com CORS habilitado para:")
for o in origins:
    logger.info(f"   - {o}")

# ============================================================
# 📦 Registro de Rotas
# ============================================================
app.include_router(auth.router, prefix="/api/auth")
app.include_router(clients.router, prefix="/api/clients")
app.include_router(company.router, prefix="/api/company")
app.include_router(uploads.router, prefix="/api/uploads")
app.include_router(dashboard.router, prefix="/api/dashboard")
app.include_router(dictionary.router, prefix="/api/dictionary")

logger.info("📡 ROTAS REGISTRADAS NO FASTAPI:")
for route in app.router.routes:
    if hasattr(route, "path"):
        logger.info(f"   - {route.path}")

# ============================================================
# 🩺 Health Check
# ============================================================
@app.get("/health")
def health_check():
    return {"status": "ok", "environment": "Render" if IS_RENDER else "Local"}

# ============================================================
# ⚠️ Tratamento global de erros
# ============================================================
@app.exception_handler(Exception)
def handle_unexpected_exception(request, exc):
    logger.exception(f"Erro inesperado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno do servidor: {str(exc)}"},
    )

# ============================================================
# 🚀 Execução (para testes locais)
# ============================================================
if __name__ == "__main__":
    import uvicorn
    logger.info("🧩 Executando AuditaSimples localmente...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=10000, reload=True)
