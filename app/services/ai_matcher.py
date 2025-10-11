"""
ai_matcher.py
--------------
Módulo simples para classificação fuzzy de produtos monofásicos
por descrição textual, sem dependência de IA paga.
"""

from rapidfuzz import fuzz
from typing import Optional, Tuple

# 🧾 Dicionário de categorias → lista de palavras-chave
# Você pode editar e expandir este dicionário facilmente.
CATEGORIAS = {
    "cerveja": ["heineken", "amstel", "skol", "brahma", "antarctica", "budweiser"],
    "refrigerante": ["coca", "coca-cola", "pepsi", "guaraná", "fanta", "sprite"],
    "água": ["água", "agua", "crystal", "bonafont", "minalba"],
    "cigarro": ["marlboro", "derby", "lucky", "chesterfield"],
    # Adicione outras categorias monofásicas conforme necessário
}

# 🧾 Mapeamento básico NCM ↔ categoria
# Você pode tornar isso mais completo no futuro.
NCM_CATEGORIA = {
    "22030000": "cerveja",         # Cervejas de malte
    "22021000": "refrigerante",   # Refrigerantes
    "22011000": "água",           # Água mineral
    "24022000": "cigarro"         # Cigarros
}

class SimpleMatcher:
    def __init__(self, categorias: dict, ncm_map: dict):
        self.categorias = categorias
        self.ncm_map = ncm_map

    def classify(self, text: str) -> Optional[Tuple[str, int]]:
        """
        Faz matching fuzzy da descrição do produto com categorias conhecidas.
        Retorna (categoria, score) se o match for forte o bastante.
        """
        text = (text or "").lower().strip()
        best_score = 0
        best_cat = None

        for cat, palavras in self.categorias.items():
            for palavra in palavras:
                score = fuzz.partial_ratio(text, palavra)
                if score > best_score:
                    best_score = score
                    best_cat = cat

        if best_score >= 70:  # Limiar configurável
            return best_cat, best_score
        return None

    def is_monofasico(self, categoria: str) -> bool:
        """
        Verifica se a categoria está dentro da lista monofásica conhecida.
        """
        return categoria in self.categorias

    def validate_ncm_for_category(self, ncm: str, categoria: str) -> dict:
        """
        Verifica se o NCM informado bate com a categoria detectada.
        Caso não haja mapeamento ou o NCM esteja vazio, retorna falso.
        """
        ncm = (ncm or "").strip()
        expected_cat = self.ncm_map.get(ncm)
        return {"ncm_valido": expected_cat == categoria}

# Instância global que pode ser importada no analysis.py
matcher = SimpleMatcher(CATEGORIAS, NCM_CATEGORIA)
