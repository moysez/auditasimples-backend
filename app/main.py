from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import Base, engine
from .auth import login_router
from .routers import clients, uploads, analyses, reports

app = FastAPI(title="AuditaSimples API", version="0.2.0")

origins = [settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(login_router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(analyses.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}
