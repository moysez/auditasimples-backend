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
    aliquota: float | None = Query(None),
    imposto_pago: float | None = Query(None),
    db: Session = Depends(get_session)
):
    try:
        # Normaliza alíquota
        if aliquota is None:
            aliquota = 0.08
        elif aliquota > 1:
            aliquota = aliquota / 100.0

        # Lê ZIP do banco
        zip_bytes = get_zip_bytes_from_db(upload_id, db)
        if not zip_bytes:
            raise FileNotFoundError("Arquivo não encontrado no banco")

        result = run_analysis_from_bytes(zip_bytes, aliquota, imposto_pago)
        # 🔁 Mantém compatibilidade com geração de relatório

        # -----------------------------
        # IA por descrição COM CATEGORIA
        # -----------------------------
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
                        "descricao": descricao,
                        "palavra": palavra,
                        "score": score,
                        "valor": valor,
                    })

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
        tax = result.get("tax_summary") or {}
        for campo in [
            "faturamento", "base_corrigida", "receita_excluida",
            "imposto_pago", "imposto_corrigido", "economia_estimada", "aliquota_utilizada"
        ]:
            if tax.get(campo) is None:
                tax[campo] = 0.0

        result["tax_summary"] = tax
        logger.info(f"✅ Tax summary sanitizado: {tax}")

        faturamento = tax.get("faturamento", result.get("total_value_sum", 0.0))
        base_corrigida = tax.get("base_corrigida", 0.0)
        receita_excluida = tax.get("receita_excluida", 0.0)
        imposto_corrigido = base_corrigida * aliquota
        imposto_pago_valor = imposto_pago or 0.0
        result["tax_summary"] = {
            "faturamento": faturamento,
            "base_corrigida": base_corrigida,
            "receita_excluida": receita_excluida,
            "imposto_pago": imposto_pago_valor,
            "imposto_corrigido": imposto_corrigido,
            "economia_estimada": economia_estimada,
            "aliquota_utilizada": aliquota,
        }
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

        return {
            "cards": {
                "documentos": result.get("documents", 0),
                "itens": result.get("items", 0),
                "valor_total": result.get("total_value_sum", 0.0),
                "economia_simulada": economia_estimada,
                "periodo": f"{result.get('period_start')} - {result.get('period_end')}"
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
                "imposto_pago": round(imposto_pago_valor, 2),
                "imposto_corrigido": round(imposto_corrigido, 2),
                "economia_estimada": economia_estimada,
                "valor_a_pagar": valor_a_pagar,
                "aliquota_utilizada": aliquota,
            }
        }

    except FileNotFoundError:
        logger.warning(f"Arquivo ZIP não encontrado para upload_id={upload_id}, client_id={client_id}")
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    except Exception as e:
        import traceback
        logger.exception(f"❌ Erro inesperado ao gerar dashboard (client_id={client_id}, upload_id={upload_id})")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório fiscal: {str(e)}")


# ------------------------------------------------------
# 📄 Endpoint para gerar e baixar o Relatório Fiscal DOCX
# ------------------------------------------------------
@router.get("/relatorio-fiscal")
def gerar_relatorio_fiscal_endpoint(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    nome_empresa: str | None = Query(None, description="Nome da empresa opcional para personalizar o relatório"),
    aliquota: float | None = Query(None),
    imposto_pago: float | None = Query(None),
    db: Session = Depends(get_session)
):
    try:
        zip_bytes = get_zip_bytes_from_db(upload_id, db)
        if not zip_bytes:
            raise FileNotFoundError("Arquivo não encontrado no banco")

        result = run_analysis_from_bytes(zip_bytes, aliquota, imposto_pago)

        if not result or len(result) == 0:
            raise ValueError("Não foi possível gerar análise a partir dos arquivos.")

        logger.info(f"🧾 DEBUG RESULT KEYS: {result.keys()}")
        logger.info(f"📊 DEBUG tax_summary: {result.get('tax_summary')}")

        client_name = nome_empresa or f"Cliente_{client_id}"
        path = gerar_relatorio_fiscal(result, client_name)

        logger.info(f"📄 Relatório gerado em: {path}")

        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"Relatorio_Fiscal_Auditoria_Monofasica_{client_name}.docx"
        )

    except FileNotFoundError:
        logger.warning(f"Arquivo ZIP não encontrado (upload_id={upload_id})")
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    except Exception as e:
        logger.exception(f"❌ Erro ao gerar relatório fiscal: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório fiscal: {str(e)}")
