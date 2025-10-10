from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from ..db import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cnpj = Column(String(255), unique=True, nullable=False)
