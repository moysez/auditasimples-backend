from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models.company import Company

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.post("/")
def create_company(owner_id: int = Form(...), cnpj: str = Form(...), nome_fantasia: str = Form(...),
                   razao_social: str = Form(None), db: Session = Depends(get_db)):
    if db.query(Company).filter_by(cnpj=cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    company = Company(owner_id=owner_id, cnpj=cnpj, nome_fantasia=nome_fantasia, razao_social=razao_social)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.get("/{owner_id}")
def list_companies(owner_id: int, db: Session = Depends(get_db)):
    return db.query(Company).filter_by(owner_id=owner_id).all()
