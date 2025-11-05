import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ============================================================
# 🔧 CARREGA VARIÁVEIS DE AMBIENTE (.env)
# ============================================================
load_dotenv()

# ============================================================
# 🌍 DETECÇÃO AUTOMÁTICA DE AMBIENTE
# ============================================================
# Render define DATABASE_URL automaticamente (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Corrige o prefixo do Render (necessário para SQLAlchemy)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"🌐 Usando banco PostgreSQL (Render): {DATABASE_URL}")
else:
    # Local MySQL (XAMPP, Laragon etc.)
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASS = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_DB = os.getenv("MYSQL_DATABASE", "auditasimples")

    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}/{MYSQL_DB}"
    print(f"💾 Usando banco MySQL local: {DATABASE_URL}")

# ============================================================
# 🧱 BASE SQLALCHEMY
# ============================================================
Base = declarative_base()

# ============================================================
# ⚙️ ENGINE E SESSÃO
# ============================================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # testa conexões mortas automaticamente
    echo=False,          # mude para True para debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================
# 🧩 FUNÇÃO DE SESSÃO (para usar com Depends)
# ============================================================
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# 🧰 FUNÇÃO OPCIONAL: CRIAR TABELAS AUTOMATICAMENTE
# ============================================================
def init_db():
    """
    Cria as tabelas no banco de dados.
    Chame essa função uma vez no main.py se quiser auto-criação.
    """
    import app.models.clients  # importa os modelos (expande conforme necessário)
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")

