from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 📦 Imports internos
from .config import settings
from .db import Base, engine, get_session

# 🔐 Auth
from .auth import router as auth_router

# 📊 Rotas principais
from .routers import clients, company

# ---------------------------------
# 1. Criação da aplicação
# ---------------------------------
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# ---------------------------------
# 2. CORS (origens autorizadas)
# ---------------------------------
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500"  # para desenvolvimento local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# 3. Banco de dados
# ---------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------
# 4. Rotas da API
# ---------------------------------
api = APIRouter(prefix="/api")

# 🔑 Autenticação
api.include_router(auth_router)

# 📌 Módulos principais
api.include_router(clients.router)
api.include_router(company.router)

# ---------------------------------
# 5. Health Checks
# ---------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {"status": "ok", "result": [row for row in result]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ---------------------------------
# 6. Registro final
# ---------------------------------
app.include_router(api)
