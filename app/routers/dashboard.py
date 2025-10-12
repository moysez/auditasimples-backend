from collections import defaultdict
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from ..db import get_session
from ..services.analysis import run_analysis_from_bytes
from ..routers.uploads import get_zip_bytes_from_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Caminho do dicionário
MONOFASICOS_FILE = Path(__file__).resolve().parent.parent / "data" / "monofasicos.json"

# -----------------------------
# Utilidades p/ IA por categoria
# -----------------------------
def load_monofasicos_map() -> dict:
    """
    Retorna um dict: {categoria: [palavras,...]}
    Ex.: {"cerveja": ["heineken","brahma",...], "refrigerante":[...]}
    """
    try:
        with open(MONOFASICOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normaliza para lower
        return {cat.lower(): [p.lower() for p in palavras] for cat, palavras in data.items()}
    except Exception as e:
        print(f"⚠️ Erro ao carregar monofasicos.json: {e}")
        return {}

def match_descricao_categoria(descricao: str, mapa: dict, limiar: int = 80):
    """
    Faz fuzzy por categoria. Percorre cada categoria e suas palavras.
    Retorna: (True/False, categoria, palavra, score)
    """
    if not descricao:
        return False, None, None, 0

    desc = descricao.lower()
    melhor = (False, None, None, 0)  # (hit, categoria, palavra, score)

    for categoria, palavras in mapa.items():
        for kw in palavras:
            score = fuzz.partial_ratio(kw, desc)
            if score > melhor[3]:
                melhor = (score >= limiar, categoria, kw, score)

    return melhor

# -----------------------------
# Endpoint
# -----------------------------
@router.get("/")
def get_dashboard(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    aliquota: float | None = Query(None),
    imposto_pago: float | None = Query(None),
    db: Session = Depends(get_session)
):
    try:
        # Normaliza alíquota (0.08 ou 8 → 0.08)
        if aliquota is None:
            aliquota = 0.08
        elif aliquota > 1:
            aliquota = aliquota / 100.0

        # Lê ZIP do banco
        zip_bytes = get_zip_bytes_from_db(upload_id, db)
        if not zip_bytes:
            raise FileNotFoundError("Arquivo não encontrado")

        # Análise base (já calcula faturamento, exclusões, etc.)
        result = run_analysis_from_bytes(zip_bytes, aliquota, imposto_pago)

        # -----------------------------
        # IA por descrição COM CATEGORIA
        # -----------------------------
        mapa = load_monofasicos_map()
        produtos = result.get("products", [])  # lista de itens com descrição e valor_total
        monofasico_desc_count = 0

        cat_counter = defaultdict(int)
        cat_examples = defaultdict(list)
        produtos_dedup = {}

        for p in produtos:
            descricao = p.get("descricao") or p.get("xProd") or ""
            valor = float(p.get("valor_total") or p.get("vProd") or 0.0)

            hit, categoria, palavra, score = match_descricao_categoria(descricao, mapa, limiar=80)
            if hit:
                monofasico_desc_count += 1
                cat_counter[categoria] += 1
                if len(cat_examples[categoria]) < 5:
                    cat_examples[categoria].append({
                        "descricao": descricao,
                        "palavra": palavra,
                        "score": score,
                        "valor": valor,
                    })

            # dedup
            key = (descricao or "").strip().lower()
            if key not in produtos_dedup:
                produtos_dedup[key] = {
                    "descricao": descricao,
                    "ocorrencias": 1,
                    "valor_total": valor
                }
            else:
                produtos_dedup[key]["ocorrencias"] += 1
                produtos_dedup[key]["valor_total"] += valor

        produtos_dedup_list = sorted(
            produtos_dedup.values(),
            key=lambda x: x["valor_total"],
            reverse=True
        )

        categorias_detectadas = []
        for categoria, count in sorted(cat_counter.items(), key=lambda kv: kv[1], reverse=True):
            categorias_detectadas.append({
                "categoria": categoria,
                "ocorrencias": count,
                "exemplos": cat_examples[categoria]
            })

        # -----------------------------
        # Ajuste no cálculo tributário
        # -----------------------------
        tax = result.get("tax_summary", {})
        faturamento = tax.get("faturamento", result.get("total_value_sum", 0.0))
        base_corrigida = tax.get("base_corrigida", 0.0)
        receita_excluida = tax.get("receita_excluida", 0.0)
        imposto_corrigido = base_corrigida * aliquota
        imposto_pago_valor = imposto_pago or 0.0

        economia_estimada = 0.0
        valor_a_pagar = 0.0

        if imposto_pago is not None:
            diferenca = imposto_pago_valor - imposto_corrigido
            if diferenca >= 0:
                economia_estimada = round(diferenca, 2)
            else:
                valor_a_pagar = round(abs(diferenca), 2)
        else:
            economia_estimada = round(receita_excluida * aliquota, 2)

        # -----------------------------
        # Resposta
        # -----------------------------
        return {
            "cards": {
                "documentos": result.get("documents", 0),
                "itens": result.get("items", 0),
                "valor_total": result.get("total_value_sum", 0.0),
                "economia_simulada": economia_estimada,
                "periodo": f"{result.get('period_start')} - {result.get('period_end')}"
            },
            "erros_fiscais": {
                "monofasico_errado": result.get("monofasico_errado", 0),
                "monofasico_desc": monofasico_desc_count,
                "monofasico_sem_ncm": result.get("monofasico_sem_ncm", 0),
                "st_corretos": result.get("st_cfop_csosn_corretos", 0),
                "st_incorretos": result.get("st_incorreta", 0),
                "categorias_detectadas": categorias_detectadas,
                "produtos_duplicados": produtos_dedup_list
            },
            "tributario": {
                "faturamento": round(faturamento, 2),
                "base_atual": round(faturamento, 2),
                "base_corrigida": round(base_corrigida, 2),
                "receita_excluida": round(receita_excluida, 2),
                "imposto_pago": round(imposto_pago_valor, 2),
                "imposto_corrigido": round(imposto_corrigido, 2),
                "economia_estimada": economia_estimada,
                "valor_a_pagar": valor_a_pagar,
                "aliquota_utilizada": aliquota,
            }
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dados do dashboard")
