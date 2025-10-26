import logging
from collections import defaultdict
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from fastapi.responses import FileResponse

from ..db import get_session
from ..services.analysis import run_analysis_from_bytes
from ..routers.uploads import get_zip_bytes_from_db
from ..services.report_docx import gerar_relatorio_fiscal

# 🧭 Configuração de logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# 📂 Caminho do dicionário
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
        return {cat.lower(): [p.lower() for p in palavras] for cat, palavras in data.items()}
    except Exception as e:
        logger.error(f"⚠️ Erro ao carregar monofasicos.json: {e}")
        return {}

def match_descricao_categoria(descricao: str, mapa: dict, limiar: int = 80):
    if not descricao:
        return False, None, None, 0

    desc = descricao.lower()
    melhor = (False, None, None, 0)

    for categoria, palavras in mapa.items():
        for kw in palavras:
            score = fuzz.partial_ratio(kw, desc)
            if score > melhor[3]:
                melhor = (score >= limiar, categoria, kw, score)

    return melhor

# -----------------------------
# Endpoint principal do Dashboard
# -----------------------------
@router.get("/")
def get_dashboard(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    aliquota: float | None = Query(None, description="Alíquota em % ou fração. Ex.: 8 ou 0.08"),
    imposto_pago: float | None = Query(None, description="Imposto pago em R$"),
    db: Session = Depends(get_session)
):
    try:
        # 1) Normalização básica de entrada
        aliq_in = None
        if aliquota is not None:
            aliq_in = float(aliquota)
            if aliq_in > 1:
                aliq_in = aliq_in / 100.0  # 8 -> 0.08

        imp_pago_in = float(imposto_pago) if imposto_pago is not None else None

        # 2) Lê ZIP do banco
        zip_bytes = get_zip_bytes_from_db(upload_id, db)
        if not zip_bytes:
            raise FileNotFoundError("Arquivo não encontrado no banco")

        # 3) Passa parâmetros para a análise:
        # - Se tem imposto pago, deixo a alíquota None para a análise não forçar um "pago" artificial.
        # - Se NÃO tem imposto pago, posso passar a alíquota (ou None → 0 nos cálculos).
        aliq_para_analise = aliq_in if imp_pago_in is None else None
        imp_para_analise = imp_pago_in if imp_pago_in is not None else None

        result = run_analysis_from_bytes(zip_bytes, aliq_para_analise, imp_para_analise)

        # 4) Coleta números base
        tax_raw = result.get("tax_summary") or {}
        faturamento = float(tax_raw.get("faturamento") or result.get("total_value_sum") or 0.0)
        receita_excluida = float(tax_raw.get("receita_excluida") or 0.0)
        base_corrigida = float(tax_raw.get("base_corrigida") or (faturamento - receita_excluida))

        # 5) Define a alíquota a usar
        #    - Se vier "aliquota" -> usa
        #    - Senão, se vier "imposto_pago" -> alíquota média (imposto_pago / faturamento, se faturamento > 0)
        #    - Senão -> 0.0
        if aliq_in is not None:
            aliq_final = aliq_in
        elif imp_pago_in is not None and faturamento > 0:
            aliq_final = imp_pago_in / faturamento
        else:
            aliq_final = 0.0

        # 6) Impostos e economia
        imposto_corrigido = base_corrigida * aliq_final
        if imp_pago_in is not None:
            diff = imp_pago_in - imposto_corrigido
            if diff >= 0:
                economia_estimada = round(diff, 2)
                valor_a_pagar = 0.0
            else:
                economia_estimada = 0.0
                valor_a_pagar = round(abs(diff), 2)
            imposto_pago_final = imp_pago_in
        else:
            economia_estimada = round(receita_excluida * aliq_final, 2)
            valor_a_pagar = 0.0
            # se não foi informado, "imposto pago" exibe 0 no dashboard
            imposto_pago_final = 0.0

        # 7) IA por descrição (mantido como estava)
        mapa = load_monofasicos_map()
        produtos = result.get("products", [])
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
                        "descricao": descricao, "palavra": palavra, "score": score, "valor": valor,
                    })

            key = (descricao or "").strip().lower()
            if key not in produtos_dedup:
                produtos_dedup[key] = {"descricao": descricao, "ocorrencias": 1, "valor_total": valor}
            else:
                produtos_dedup[key]["ocorrencias"] += 1
                produtos_dedup[key]["valor_total"] += valor

        produtos_dedup_list = sorted(produtos_dedup.values(), key=lambda x: x["valor_total"], reverse=True)
        categorias_detectadas = [
            {"categoria": cat, "ocorrencias": count, "exemplos": cat_examples[cat]}
            for cat, count in sorted(cat_counter.items(), key=lambda kv: kv[1], reverse=True)
        ]

        # 8) Persistimos um tax_summary FINAL (consistente para o front e para o DOCX se quiser reaproveitar)
        result["tax_summary"] = {
            "faturamento": round(faturamento, 2),
            "base_corrigida": round(base_corrigida, 2),
            "receita_excluida": round(receita_excluida, 2),
            "imposto_pago": round(imposto_pago_final, 2),
            "imposto_corrigido": round(imposto_corrigido, 2),
            "economia_estimada": round(economia_estimada, 2),
            "aliquota_utilizada": round(aliq_final, 6),  # fração (0.08 = 8%)
        }
        logger.info(f"🧪 TAX SUMMARY FINAL: {result['tax_summary']}")

        return {
            "cards": {
                "documentos": result.get("documents", 0),
                "itens": result.get("items", 0),
                "valor_total": round(result.get("total_value_sum", 0.0), 2),
                "economia_simulada": economia_estimada,
                "periodo": f"{result.get('period_start')} - {result.get('period_end')}",
            },
            "erros_fiscais": {
                "monofasico_ncm_incorreto": result.get("monofasico_sem_ncm", 0),
                "monofasico_sem_ncm": result.get("monofasico_sem_ncm", 0),
                "monofasico_desc": monofasico_desc_count,
                "st_corretos": result.get("st_cfop_csosn_corretos", 0),
                "st_incorretos": result.get("st_incorreta", 0),
                "categorias_detectadas": categorias_detectadas,
                "produtos_duplicados": produtos_dedup_list,
            },
            "tributario": {
                "faturamento": round(faturamento, 2),
                "base_atual": round(faturamento, 2),
                "base_corrigida": round(base_corrigida, 2),
                "receita_excluida": round(receita_excluida, 2),
                "imposto_pago": round(imposto_pago_final, 2),
                "imposto_corrigido": round(imposto_corrigido, 2),
                "economia_estimada": economia_estimada,
                "valor_a_pagar": valor_a_pagar,
                "aliquota_utilizada": aliq_final,  # fração
            },
        }

    except FileNotFoundError:
        logger.warning(f"Arquivo ZIP não encontrado para upload_id={upload_id}, client_id={client_id}")
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    except Exception as e:
        logger.exception(f"❌ Erro inesperado ao gerar dashboard (client_id={client_id}, upload_id={upload_id})")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório fiscal: {str(e)}")
