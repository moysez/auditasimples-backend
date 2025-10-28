"""
ai_matcher.py
--------------
Classificador leve para itens monofásicos usando listas do JSON
e fuzzy matching seguro (RapidFuzz), evitando falsos positivos.
"""

from typing import Optional, Tuple, Dict, List
from rapidfuzz import fuzz
import json
import os
import re
import unicodedata

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MONO_PATH = os.path.normpath(os.path.join(DATA_DIR, "monofasicos.json"))
NCM_PATH  = os.path.normpath(os.path.join(DATA_DIR, "ncm_catalog.json"))

def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.category(ch).startswith("M"))
    return s

class JsonMatcher:
    """
    Estrutura do monofasicos.json esperada:
    {
      "cerveja": ["heineken","amstel","skol",...],
      "refrigerante": ["coca","coca-cola","pepsi",...],
      ...
    }

    Estrutura do ncm_catalog.json esperada:
    {
      "22030000": "cerveja",
      "22021000": "refrigerante",
      ...
    }
    """
    def __init__(self, mono_path: str = MONO_PATH, ncm_path: str = NCM_PATH):
        with open(mono_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # normaliza chaves e keywords
        self.categorias: Dict[str, List[str]] = {
            _norm(cat): list({_norm(w) for w in words if _norm(w)})
            for cat, words in raw.items()
        }

        with open(ncm_path, "r", encoding="utf-8") as f:
            ncm_raw = json.load(f)
        self.ncm_map: Dict[str, str] = {str(k).strip(): _norm(v) for k, v in ncm_raw.items()}

        # compila regex por palavra (match de token exato)
        self._token_regex: Dict[str, List[re.Pattern]] = {
            cat: [re.compile(rf"\b{re.escape(w)}\b") for w in words if len(w) >= 3]
            for cat, words in self.categorias.items()
        }

    def classify(self, text: str) -> Optional[Tuple[str, int]]:
        """
        1) tenta token boundary (regex) para cada palavra-chave
        2) fallback: fuzzy token_sort_ratio com limiar alto
        Evita falsos positivos como 'pizza'≈'pepsi'.
        """
        t = _norm(text)
        best_cat, best_score = None, 0

        for cat, patterns in self._token_regex.items():
            # regra 1 — token exato
            for rgx in patterns:
                if rgx.search(t):
                    return cat, 100

            # regra 2 — fuzzy forte (≥ 88) em qualquer palavra da categoria
            for w in self.categorias[cat]:
                if len(w) < 4:
                    continue
                score = fuzz.token_sort_ratio(t, w)
                if score > best_score:
                    best_score, best_cat = score, cat

        if best_score >= 88:
            return best_cat, best_score
        return None

    def is_monofasico(self, categoria: str) -> bool:
        return _norm(categoria) in self.categorias

    def validate_ncm_for_category(self, ncm: str, categoria: str) -> dict:
        ncm = (ncm or "").strip()
        expected_cat = self.ncm_map.get(ncm)
        return {"ncm_valido": expected_cat == _norm(categoria)}

# Instância global (importada no analysis.py)
matcher = JsonMatcher()
