from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

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
    created_at: datetime
    class Config:
        orm_mode = True

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
