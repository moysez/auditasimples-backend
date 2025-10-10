from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_session
from .auth import login_router
from .routers import clients, company  # 👈 importamos aqui

app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# 🌐 CORS
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Banco
Base.metadata.create_all(bind=engine)

# 📌 Rotas da API
api = APIRouter(prefix="/api")
api.include_router(login_router)
api.include_router(clients.router)   # 👈 agora registradas
api.include_router(company.router)

# 🩺 Health checks
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

# 🔗 Inclui o roteador principal
app.include_router(api)
