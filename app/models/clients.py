from sqlalchemy import Column, Integer, String
from ..db import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)  # ✅ substituímos email por cnpj
