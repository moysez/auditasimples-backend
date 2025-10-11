from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json
import unicodedata
from rapidfuzz import fuzz

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "ncm_catalog.json"

def _normalize(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.split())

class SemanticNCMMatcher:
    """
    Matching semântico leve (fuzzy) 100% local:
      - classifica a descrição em uma categoria (cerveja, refrigerante, etc.)
      - valida NCM por prefixo permitido por categoria (editável no JSON)
    """

    def __init__(self, threshold: int = 85):
        self.threshold = threshold
        self.catalog: Dict[str, Dict[str, Any]] = {}

    def load(self, path: Path = CATALOG_PATH) -> None:
        with open(path, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)

        # pré-normaliza palavras
        for cat, cfg in self.catalog.items():
            cfg["__palavras_norm__"] = [_normalize(w) for w in cfg.get("palavras", [])]

    def classify(self, descricao: str) -> Optional[Tuple[str, int]]:
        """
        Retorna (categoria, score) se atingir o threshold, senão None.
        """
        d = _normalize(descricao)
        if not d or not self.catalog:
            return None

        best_cat, best_score = None, -1
        for cat, cfg in self.catalog.items():
            for kw in cfg.get("__palavras_norm__", []):
                score = fuzz.partial_ratio(d, kw)
                if score > best_score:
                    best_cat, best_score = cat, score

        if best_cat and best_score >= self.threshold:
            return best_cat, best_score
        return None

    def validate_ncm_for_category(self, ncm: str, categoria: str) -> Dict[str, Any]:
        """
        Verifica se NCM (8 dígitos) bate com os prefixos válidos da categoria.
        """
        n = (ncm or "").strip()
        result = {
            "ncm_valido": False,
            "motivo": None
        }
        if len(n) != 8 or not n.isdigit():
            result["motivo"] = "NCM ausente ou inválido"
            return result

        cfg = self.catalog.get(categoria) or {}
        prefixes = cfg.get("ncm_prefixos_validos", [])
        if not prefixes:
            # Se não tiver regra no catálogo, não acusa erro
            result["ncm_valido"] = True
            return result

        if any(n.startswith(p) for p in prefixes):
            result["ncm_valido"] = True
            return result

        result["motivo"] = f"NCM {n} não pertence à categoria '{categoria}'"
        return result

    def is_monofasico(self, categoria: Optional[str]) -> bool:
        if not categoria:
            return False
        cfg = self.catalog.get(categoria) or {}
        return bool(cfg.get("monofasico", False))


# Singleton simples para reuso
matcher = SemanticNCMMatcher()
try:
    matcher.load()
except Exception as e:
    # Em produção, logue isso com loguru caso queira
    print(f"[ai_matcher] Falha ao carregar catálogo: {e}")
