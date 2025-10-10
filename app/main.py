from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# 📦 Importações internas
from .config import settings
from .db import Base, engine
from .models.user import User
from .models.company import Company
from .models.upload import Upload
from .models.report import Report
from .routers import auth, company, uploads, dashboard, reports

# -----------------------------
# 1. Criação da aplicação
# -----------------------------
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# -----------------------------
# 2. Configuração de CORS
# -----------------------------
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Pode trocar por ["*"] se for liberar geral
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# -----------------------------
# 3. Inicialização do banco de dados
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# 4. Registro das rotas
# -----------------------------
api = APIRouter(prefix="/api")

api.include_router(auth.router)
api.include_router(company.router)
api.include_router(uploads.router)
api.include_router(dashboard.router)
api.include_router(reports.router)

app.include_router(api)

# -----------------------------
# 5. Health check
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
