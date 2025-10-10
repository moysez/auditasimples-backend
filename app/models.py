from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, JSON
from datetime import datetime
from .db import Base

# 👤 Usuário
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

# 🏢 Empresa
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    cnpj = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 📤 Upload de Arquivos ZIP
class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_data = Column(LargeBinary, nullable=False)  # 🆕 Salva arquivo direto no banco
    created_at = Column(DateTime, default=datetime.utcnow)

# 📊 Relatórios / Análises
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
