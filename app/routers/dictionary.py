from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path

# 📍 Caminho do arquivo de dicionário
DICTIONARY_FILE = Path(__file__).resolve().parent.parent / "data" / "monofasicos.json"

router = APIRouter(
    prefix="/dictionary",
    tags=["Dictionary"]
)

# 📥 Modelo de entrada
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
def update_dictionary(payload: DictionaryUpdate):
    """
    Adiciona ou atualiza uma categoria no dicionário monofásico.
    """
    try:
        data = load_dictionary()
        categoria = payload.categoria.lower().strip()
        palavras = [p.lower().strip() for p in payload.palavras]

        if categoria in data:
            # Evita duplicar palavras
            existentes = set(data[categoria])
            novas = existentes.union(palavras)
            data[categoria] = sorted(list(novas))
        else:
            data[categoria] = sorted(list(set(palavras)))

        save_dictionary(data)
        return {"message": f"Categoria '{categoria}' atualizada com sucesso.", "total_palavras": len(data[categoria])}
    except Exception as e:
        print(f"❌ Erro ao atualizar dicionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar dicionário")

@router.get("/")
def get_dictionary():
    """
    Retorna o conteúdo atual do dicionário monofásico.
    """
    try:
        return load_dictionary()
    except Exception as e:
        print(f"❌ Erro ao carregar dicionário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dicionário")
