from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..db import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=False)
    nome_fantasia = Column(String(255), nullable=False)
    razao_social = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
