from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 📦 Rotas
from .routers import clients, company, uploads, dashboard, dictionary

# ⚙️ Configurações e DB
from .config import settings
from .db import Base, engine, get_session

# 🧾 Relatório DOCX
from fastapi.responses import FileResponse
from app.services.analysis import run_analysis_from_bytes
from app.services.report_docx import gerar_relatorio_fiscal

# 🔐 Autenticação
from .auth import router as auth_router

# 🪵 Logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)  # ✅ Instância global do logger

# 🧠 Inicializa app
app = FastAPI(
    title="AuditaSimples API",
    version="1.0.0"
)

# 🌐 CORS
origins = [
    "https://auditasimples.io",
    "https://www.auditasimples.io",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Banco de dados
Base.metadata.create_all(bind=engine)

# 📍 Prefixo de API
api = APIRouter(prefix="/api")

# 📊 Rotas principais
api.include_router(clients.router)
api.include_router(company.router)
api.include_router(uploads.router)
api.include_router(auth_router)
api.include_router(dashboard.router)
api.include_router(dictionary.router)

# 🩺 Health Check
@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

# 🧪 Teste de conexão com DB
@app.get("/db-check")
def check_db(session: Session = Depends(get_session)):
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return {"status": "ok", "result": [row for row in result]}
    except Exception as e:
        logger.exception("❌ Erro ao verificar conexão com o banco:")
        return {"status": "error", "detail": str(e)}

# 🧾 Geração de Relatório DOCX (exemplo simples)
@app.get("/api/relatorio/")
def gerar_relatorio(client_id: int):
    """
    Gera e retorna o arquivo DOCX com o relatório fiscal monofásico.
    ⚠️ Substituir zip_bytes pela lógica real de recuperação dos XMLs.
    """
    zip_bytes = b""  # 👉 Placeholder temporário
    totals = run_analysis_from_bytes(zip_bytes)
    path = gerar_relatorio_fiscal(totals, client_name=f"Cliente {client_id}")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Relatorio_Fiscal_Auditoria_Monofasica.docx"
    )

# 📌 Registra o roteador principal
app.include_router(api)

# 🧭 Log de rotas no console (Render)
logger.info("📜 ROTAS REGISTRADAS NO FASTAPI:")
for route in app.routes:
    logger.info(route.path)
logger.info("📜 FIM DAS ROTAS")
