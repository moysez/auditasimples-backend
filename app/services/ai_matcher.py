import json
import os
import difflib

# Caminho do JSON com as categorias monofásicas
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "monofasicos.json")

# Tabela de NCM monofásicos por categoria (exemplo inicial)
# Pode evoluir depois com dados oficiais (Bebidas Frias, Cigarros, Combustíveis, etc.)
NCM_MAP = {
    "cerveja": ["22030000", "22029100"],
    "refrigerante": ["22021000", "22029000"],
    "agua": ["22011000"],
    "cigarro": ["24022000"]
}

# Carregar dicionário de palavras-chave do arquivo JSON
with open(DATA_PATH, "r", encoding="utf-8") as f:
    KEYWORDS = json.load(f)

# Transformar em lookup plano para fuzzy match
FLAT_KEYWORDS = []
for cat, words in KEYWORDS.items():
    for w in words:
        FLAT_KEYWORDS.append((w.lower(), cat))


# -------------------------------------------
# 🔸 Função: classificação por descrição
# -------------------------------------------
def classify(description: str, min_ratio: float = 0.75):
    """
    Faz fuzzy matching com as palavras cadastradas em monofasicos.json.
    Retorna (categoria, score) ou None.
    """
    desc_lower = description.lower()
    best_match = None
    best_ratio = 0

    for kw, cat in FLAT_KEYWORDS:
        ratio = difflib.SequenceMatcher(None, kw, desc_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = cat

    if best_ratio >= min_ratio:
        return best_match, best_ratio
    return None


# -------------------------------------------
# 🔸 Função: validação se categoria é monofásica
# -------------------------------------------
def is_monofasico(category: str) -> bool:
    """
    Checa se a categoria identificada é monofásica
    """
    return category in KEYWORDS


# -------------------------------------------
# 🔸 Função: validação de NCM vs categoria
# -------------------------------------------
def validate_ncm_for_category(ncm: str, category: str):
    """
    Valida se o NCM informado pertence ao conjunto esperado da categoria.
    """
    ncm = (ncm or "").replace(".", "").strip()
    expected = NCM_MAP.get(category, [])

    return {
        "ncm_valido": ncm in expected,
        "ncm_informado": ncm,
        "ncm_esperado": expected
    }


# -------------------------------------------
# 📌 Debug / teste manual
# -------------------------------------------
if __name__ == "__main__":
    tests = [
        "Cerveja Heineken 600ml",
        "Refri Coca Cola 2L",
        "Agua Mineral Crystal",
        "Cigarro Derby"
    ]

    for t in tests:
        result = classify(t)
        print(f"{t} => {result}")
