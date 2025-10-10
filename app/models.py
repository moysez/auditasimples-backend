from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from datetime import datetime
from .db import Base

# 👤 Usuários
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

# 🏢 Empresas / Clientes
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    cnpj = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 📥 Uploads de Arquivos
class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🧾 Relatórios Gerados
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🤖 Jobs de Análise (opcional)
class AnalysisJob(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    status = Column(String(50), default="queued")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
