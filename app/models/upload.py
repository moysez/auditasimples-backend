from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy import LargeBinary
from ..db import Base
from sqlalchemy.sql import func

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
