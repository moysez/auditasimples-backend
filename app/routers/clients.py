from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..db import get_session
from ..models.clients import Client

router = APIRouter(
    tags=["Clients"]
)

# 🧾 Schemas de entrada e saída
class ClientCreate(BaseModel):
    name: str
    cnpj: str

class ClientOut(BaseModel):
    id: int
    name: str
    cnpj: str

    class Config:
        orm_mode = True

# 📌 Criar cliente
@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_session)):
    # Verifica se já existe cliente com esse CNPJ
    existing = db.query(Client).filter(Client.cnpj == payload.cnpj).first()
    if existing:
        raise HTTPException(status_code=400, detail="Empresa já cadastrada")

    client = Client(name=payload.name, cnpj=payload.cnpj)
    db.add(client)
    db.commit()
    db.refresh(client)

    return client

# 📌 Listar clientes
@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_session)):
    clients = db.query(Client).all()
    return clients

# 📌 Buscar cliente por ID
@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_session)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client

# 📌 Deletar cliente
@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_session)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
    return {"ok": True, "message": "Cliente deletado com sucesso"}
