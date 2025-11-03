from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, func
from sqlalchemy.orm import relationship
from app.db import Base

# ============================================================
# 👤 MODELO DE USUÁRIO
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# 🧾 MODELO DE CLIENTES
# ============================================================
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    document = Column(String(20), unique=True, nullable=False)  # CNPJ ou CPF
    email = Column(String(120))
    phone = Column(String(20))
    address = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# 🏢 MODELO DE EMPRESAS
# ============================================================
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    corporate_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    cnpj = Column(String(20), unique=True, nullable=False)
    regime = Column(String(50))  # Simples, Lucro Presumido etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# 📚 DICIONÁRIO DE PRODUTOS / NCM / CFOP
# ============================================================
class Dictionary(Base):
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True, index=True)
    ncm = Column(String(20), index=True)
    cfop = Column(String(20))
    cst = Column(String(10))
    description = Column(Text)
    tax_type = Column(String(50))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================
# 📤 UPLOADS (NF-e, NFC-e, SAT)
# ============================================================

class Upload(Base):
    __tablename__ = "uploads"

    id          = Column(Integer, primary_key=True, index=True)
    client_id   = Column(Integer, nullable=False, index=True)
    filename    = Column(String(255), nullable=False)
    filepath    = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)

# ============================================================
# 🧮 LOG DE AUDITORIAS / AÇÕES
# ============================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    details = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
