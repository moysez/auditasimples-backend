from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth

# ============================================================
# 🚀 CRIAÇÃO DO APP
# ============================================================

app = FastAPI(
    title="AuditaSimples API",
    description="API fiscal e tributária do AuditaSimples (versão simples, sem banco)",
    version="1.0.0",
)

# ============================================================
# 🌐 CORS
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

# /api/auth/login
app.include_router(auth.router, prefix="/api/auth")


# ============================================================
# 🩺 HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AuditaSimples API funcionando corretamente (sem banco)"}
