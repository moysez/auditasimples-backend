from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    cnpj = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="client")
    analyses = relationship("AnalysisJob", back_populates="client")
    reports = relationship("Report", back_populates="client")

class Upload(Base):
    from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
    from datetime import datetime
    from .db import Base
    
    class Upload(Base):
        __tablename__ = "uploads"
        id = Column(Integer, primary_key=True)
        client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
        filename = Column(String(255), nullable=False)
        file_data = Column(LargeBinary, nullable=False)  # <-- salvamos o arquivo aqui
        created_at = Column(DateTime, default=datetime.utcnow)
        
class AnalysisJob(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    status = Column(String(50), default="queued")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="analyses")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    findings = Column(JSON, default={})
    totals = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="reports")
