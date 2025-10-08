from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_session
from ..models import Client
from ..schemas import ClientCreate, ClientOut
from ..auth import get_current_user
from typing import List

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_session), user=Depends(get_current_user)):
    c = Client(name=payload.name, cnpj=payload.cnpj)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_session), user=Depends(get_current_user)):
    return db.query(Client).order_by(Client.id.desc()).all()
