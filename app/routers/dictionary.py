from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
from pathlib import Path

# Importa autenticação
from ..routers.auth import get_current_user

# 📍 Caminho do arquivo do dicionário
DICTIONARY_FILE = Path(__file__).resolve().parent.parent / "data" / "monofasicos.json"
router = APIRouter()

@router.get("/")
def dictionary_root():
    # Mantido para compatibilidade — preencha à vontade depois.
    return {"status": "ok"}

class DictionaryUpdate(BaseModel):
    categoria: str
    palavras: list[str]

def load_dictionary():
    if not DICTIONARY_FILE.exists():
        return {}
    with open(DICTIONARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dictionary(data):
    with open(DICTIONARY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@router.post("/update")
def update_dictionary(payload: DictionaryUpdate, user: dict = Depends(get_current_user)):
    """
    🔐 Atualiza o dicionário de monofásicos — apenas com autenticação.
    """
    try:
        data = load_dictionary()
        categoria = payload.categoria.lower().strip()
        palavras = [p.lower().strip() for p in payload.palavras]

        if categoria in data:
            existentes = set(data[categoria])
            novas = existentes.union(palavras)
            data[categoria] = sorted(list(novas))
        else:
            data[categoria] = sorted(list(set(palavras)))

        save_dictionary(data)
        return {
            "message": f"Categoria '{categoria}' atualizada com sucesso.",
            "total_palavras": len(data[categoria]),
            "user": user["username"]  # opcional: logar quem atualizou
        }
    except Exception as e:
        print(f"❌ Erro ao atualizar dicionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar dicionário")

@router.get("/")
def get_dictionary(user: dict = Depends(get_current_user)):
    """
    🔐 Retorna o dicionário (também exige autenticação).
    """
    try:
        return load_dictionary()
    except Exception as e:
        print(f"❌ Erro ao carregar dicionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dicionário")
