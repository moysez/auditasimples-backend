from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from ..db import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(50), default="admin")  # admin por padrão neste estágio
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
