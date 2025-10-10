from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..db import Base

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
