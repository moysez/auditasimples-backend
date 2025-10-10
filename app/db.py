from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# ===========================
# 📌 URL do Banco de Dados
# ===========================
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./auditasimples.db"

# Para SQLite precisamos de connect_args especiais
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# ===========================
# 🧱 Engine e Session
# ===========================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True
)

Base = declarative_base()

# ===========================
# 💡 Dependência de sessão (para rotas)
# ===========================
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
