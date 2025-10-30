import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usa DATABASE_URL se existir (Render/Prod). Senão, um SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auditassimples.db")

# Render geralmente usa Postgres; aceitamos tanto sqlite quanto postgres.
# Para Postgres no Render, a URL costuma vir com sslmode=require e driver psycopg.
# SQLAlchemy lida com ambos; não forçamos driver específico aqui.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

# Dependência FastAPI — **nome estável** usado por todos os routers
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
