from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_session
from ..models.company import Company
from ..models.clients import Client

router = APIRouter(
    tags=["Companies"]
)

# 📌 Criar empresa vinculada a um cliente
@router.post("/", response_model=dict)
def create_company(client_id: int, name: str, cnpj: str, db: Session = Depends(get_session)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    existing = db.query(Company).filter(Company.cnpj == cnpj).first()
    if existing:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

    company = Company(client_id=client_id, name=name, cnpj=cnpj)
    db.add(company)
    db.commit()
    db.refresh(company)
    return {"id": company.id, "name": company.name, "cnpj": company.cnpj}

# 📌 Listar empresas
@router.get("/", response_model=List[dict])
def list_companies(db: Session = Depends(get_session)):
    companies = db.query(Company).all()
    return [{"id": c.id, "name": c.name, "cnpj": c.cnpj, "client_id": c.client_id} for c in companies]

# 📌 Buscar empresa por ID
@router.get("/{company_id}", response_model=dict)
def get_company(company_id: int, db: Session = Depends(get_session)):
    company = db.query(Company).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"id": company.id, "name": company.name, "cnpj": company.cnpj, "client_id": company.client_id}

# 📌 Deletar empresa
@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_session)):
    company = db.query(Company).get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    db.delete(company)
    db.commit()
    return {"ok": True, "message": "Empresa deletada com sucesso"}
