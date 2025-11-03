import hashlib
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine, Base
from app.models import User

def hash_password(password: str) -> str:
    """Gera hash SHA256 da senha."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_admin():
    """Cria usuário admin padrão, se não existir."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("✅ Usuário admin já existe.")
            return

        hashed_pwd = hash_password("102030*")
        admin_user = User(
            username="admin",
            email="admin@auditasimples.io",
            hashed_password=hashed_pwd,
            is_active=True,
            role="admin",
        )

        db.add(admin_user)
        db.commit()
        print("✅ Usuário admin criado com sucesso!")
        print("👤 Login: admin")
        print("🔑 Senha: 102030*")
    except Exception as e:
        print("❌ Erro ao criar admin:", e)
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
