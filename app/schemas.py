from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class ClientCreate(BaseModel):
    name: str
    cnpj: Optional[str] = None

class ClientOut(BaseModel):
    id: int
    name: str
    cnpj: Optional[str] = None
    class Config:
        from_attributes = True

class UploadOut(BaseModel):
    id: int
    client_id: int
    filename: str
    storage_key: str
    class Config:
        from_attributes = True

class AnalysisOut(BaseModel):
    id: int
    client_id: int
    upload_id: int
    status: str
    summary: Optional[str] = None
    class Config:
        from_attributes = True

class ReportOut(BaseModel):
    id: int
    client_id: int
    analysis_id: int
    title: str
    findings: Dict[str, Any]
    totals: Dict[str, Any]
    class Config:
        from_attributes = True
