from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from datetime import datetime
from ..db import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    data = Column(JSON, nullable=False)  # guarda os resultados da análise
    created_at = Column(DateTime, default=datetime.utcnow)
