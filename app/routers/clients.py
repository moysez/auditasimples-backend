from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from ..db import get_session
from ..models.clients import Client

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

# 📌 Criar cliente
@router.post("/", response_model=dict)
def create_client(
    name: str = Form(...),
    cnpj: str = Form(...),
    db: Session = Depends(get_session)
):
    # Verifica se já existe cliente com esse CNPJ
    existing = db.query(Client).filter(Client.cnpj == cnpj).first()
    if existing:
        raise HTTPException(status_code=400, detail="Empresa já cadastrada")

    client = Client(name=name, cnpj=cnpj)
    db.add(client)
    db.commit()
    db.refresh(client)

    return {"id": client.id, "name": client.name, "cnpj": client.cnpj}

# 📌 Listar clientes
@router.get("/", response_model=List[dict])
def list_clients(db: Session = Depends(get_session)):
    clients = db.query(Client).all()
    return [{"id": c.id, "name": c.name, "cnpj": c.cnpj} for c in clients]

# 📌 Buscar cliente por ID
@router.get("/{client_id}", response_model=dict)
def get_client(client_id: int, db: Session = Depends(get_session)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {"id": client.id, "name": client.name, "cnpj": client.cnpj}

# 📌 Deletar cliente
@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_session)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
    return {"ok": True, "message": "Cliente deletado com sucesso"}
