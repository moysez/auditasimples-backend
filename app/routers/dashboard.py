import logging
import json
import os
from collections import defaultdict
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from app.models import Upload
from ..db import get_session
from ..services.analysis import run_analysis_from_bytes
from ..services.report_docx import gerar_relatorio_fiscal

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

router = APIRouter(tags=["Dashboard"])
MONOFASICOS_FILE = Path(__file__).resolve().parent.parent / "data" / "monofasicos.json"
IS_RENDER = os.getenv("ENV") == "render"

def load_monofasicos_map() -> dict:
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

# ============================================================
# 📊 DASHBOARD
# ============================================================
@router.get("/")
def get_dashboard(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    aliquota: float | None = Query(None),
    imposto_pago: float | None = Query(None),
    db: Session = Depends(get_session)
):
    try:
        aliq_in = float(aliquota) / 100 if aliquota and aliquota > 1 else aliquota
        imp_pago_in = float(imposto_pago) if imposto_pago is not None else None

        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload não encontrado")

        if IS_RENDER:
            logger.warning(f"🧱 Ignorando leitura local no Render: {upload.filepath}")
            raise HTTPException(status_code=400, detail="Execução local não disponível no ambiente Render.")

        if not os.path.exists(upload.filepath):
            raise HTTPException(status_code=404, detail=f"Arquivo local não encontrado: {upload.filepath}")

        with open(upload.filepath, "rb") as f:
            zip_bytes = f.read()

        aliq_para_analise = aliq_in if imp_pago_in is None else None
        imp_para_analise = imp_pago_in if imp_pago_in is not None else None
        result = run_analysis_from_bytes(zip_bytes, aliq_para_analise, imp_para_analise)

        tax_raw = result.get("tax_summary") or {}
        faturamento = float(tax_raw.get("faturamento") or result.get("total_value_sum") or 0.0)
        receita_excluida = float(tax_raw.get("receita_excluida") or 0.0)
        base_corrigida = faturamento - receita_excluida
        aliq_final = aliq_in or (imp_pago_in / faturamento if imp_pago_in and faturamento > 0 else 0.0)
        imposto_corrigido = base_corrigida * aliq_final

        if imp_pago_in:
            diff = imp_pago_in - imposto_corrigido
            economia_estimada = max(round(diff, 2), 0)
            valor_a_pagar = abs(min(round(diff, 2), 0))
        else:
            economia_estimada = round(receita_excluida * aliq_final, 2)
            valor_a_pagar = 0.0

        mapa = load_monofasicos_map()
        produtos = result.get("products", [])
        monofasico_desc_count = 0
        cat_counter = defaultdict(int)
        cat_examples = defaultdict(list)
        produtos_dedup = {}

        for p in produtos:
            descricao = p.get("descricao") or p.get("xProd") or ""
            valor = float(p.get("valor_total") or p.get("vProd") or 0.0)
            hit, categoria, palavra, score = match_descricao_categoria(descricao, mapa, 80)
            if hit:
                monofasico_desc_count += 1
                cat_counter[categoria] += 1
                if len(cat_examples[categoria]) < 5:
                    cat_examples[categoria].append(
                        {"descricao": descricao, "palavra": palavra, "score": score, "valor": valor}
                    )
            key = descricao.strip().lower()
            produtos_dedup[key] = produtos_dedup.get(key, {"descricao": descricao, "ocorrencias": 0, "valor_total": 0})
            produtos_dedup[key]["ocorrencias"] += 1
            produtos_dedup[key]["valor_total"] += valor

        result["tax_summary"] = {
            "faturamento": round(faturamento, 2),
            "base_corrigida": round(base_corrigida, 2),
            "receita_excluida": round(receita_excluida, 2),
            "imposto_corrigido": round(imposto_corrigido, 2),
            "economia_estimada": round(economia_estimada, 2),
            "aliquota_utilizada": round(aliq_final, 6),
        }

        return {
            "cards": {
                "documentos": result.get("documents", 0),
                "itens": result.get("items", 0),
                "valor_total": round(result.get("total_value_sum", 0.0), 2),
                "economia_simulada": economia_estimada,
                "periodo": f"{result.get('period_start')} - {result.get('period_end')}",
            },
            "erros_fiscais": {
                "monofasico_desc": monofasico_desc_count,
                "categorias_detectadas": [
                    {"categoria": cat, "ocorrencias": count, "exemplos": cat_examples[cat]}
                    for cat, count in sorted(cat_counter.items(), key=lambda kv: kv[1], reverse=True)
                ],
                "produtos_duplicados": sorted(produtos_dedup.values(), key=lambda x: x["valor_total"], reverse=True),
            },
            "tributario": result["tax_summary"],
        }

    except Exception as e:
        logger.exception("❌ Erro inesperado ao gerar dashboard")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório fiscal: {str(e)}")


# ============================================================
# 📄 RELATÓRIO DOCX
# ============================================================
@router.get("/relatorio-fiscal")
def get_relatorio_fiscal_docx(
    client_id: int = Query(...),
    upload_id: int = Query(...),
    aliquota: float | None = Query(None),
    imposto_pago: float | None = Query(None),
    db: Session = Depends(get_session)
):
    try:
        aliq_in = float(aliquota) / 100 if aliquota and aliquota > 1 else aliquota
        imp_pago_in = float(imposto_pago) if imposto_pago is not None else None
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload não encontrado")

        if IS_RENDER:
            raise HTTPException(status_code=400, detail="Leitura local indisponível em produção (Render).")

        if not os.path.exists(upload.filepath):
            raise HTTPException(status_code=404, detail=f"Arquivo local não encontrado: {upload.filepath}")

        with open(upload.filepath, "rb") as f:
            zip_bytes = f.read()

        result = run_analysis_from_bytes(zip_bytes, aliq_in, imp_pago_in)
        file_path = gerar_relatorio_fiscal(totals=result, client_name=f"Cliente {client_id}", cnpj="00.000.000/0000-00")

        return FileResponse(
            path=file_path,
            filename=file_path.split("/")[-1],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        logger.exception("❌ Erro ao gerar DOCX")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DOCX: {str(e)}")
