from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .auth import login_router
from .routers import clients, uploads, analyses, reports, dashboard

# 🔹 Criação da aplicação
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# 🔸 CORS
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5500"  # opcional - ambiente local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Criar tabelas automaticamente no banco de dados
Base.metadata.create_all(bind=engine)

# 🔸 Rotas principais
api = APIRouter(prefix="/api")
api.include_router(login_router)
api.include_router(clients.router)
api.include_router(uploads.router)
api.include_router(analyses.router)
api.include_router(reports.router)
api.include_router(dashboard.router)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

app.include_router(api)
