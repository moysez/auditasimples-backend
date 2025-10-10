from __future__ import annotations
from typing import Dict, Any
import zipfile
import io
from datetime import datetime

from .nfe import parse_nfe_xml
from ..services.storage import get_zip_path

# Palavras-chave para identificar produtos monofásicos
KEYWORDS_MONO = [
    'refrigerante', 'coca', 'coca-cola', 'cerveja', 'skol', 'brahma', 'antarctica',
    'guaraná', 'guarana', 'pepsi', 'heineken', 'amstel'
]

# ===========================
# 🔸 Funções utilitárias
# ===========================
def _is_monofasico_by_desc(desc: str) -> bool:
    d = (desc or '').lower()
    return any(k in d for k in KEYWORDS_MONO)

def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

# ===========================
# 📊 Função de análise principal (base)
# ===========================
def _run_analysis_from_zipfile(zf: zipfile.ZipFile) -> Dict[str, Any]:
    totals = {
        "documents": 0,
        "items": 0,
        "total_value_sum": 0.0,
        "period_start": None,
        "period_end": None,
        "monofasico_sem_ncm": 0,
        "monofasico_palavra_chave": 0,
        "st_cfop_csosn_corretos": 0,
        "st_incorreta": 0
    }

    for name in zf.namelist():
        if not name.lower().endswith(".xml"):
            continue

        try:
            xml_bytes = zf.read(name)
        except Exception:
            continue

        try:
            doc = parse_nfe_xml(xml_bytes)
        except Exception:
            continue

        totals["documents"] += 1
        totals["total_value_sum"] += doc.get("total_value", 0.0)

        dt = doc.get("issue_date")
        if dt:
            if totals["period_start"] is None or dt < totals["period_start"]:
                totals["period_start"] = dt
            if totals["period_end"] is None or dt > totals["period_end"]:
                totals["period_end"] = dt

        for item in doc.get("items", []):
            totals["items"] += 1
            desc = item.get("xProd", "")
            ncm = item.get("ncm", "")
            cfop = item.get("cfop", "")
            csosn = item.get("csosn", "")

            if _is_monofasico_by_desc(desc):
                totals["monofasico_palavra_chave"] += 1
                if not _has_valid_ncm(ncm):
                    totals["monofasico_sem_ncm"] += 1

            if cfop == "5405" and csosn == "500":
                totals["st_cfop_csosn_corretos"] += 1
            else:
                totals["st_incorreta"] += 1

    # Formatar datas
    if totals["period_start"]:
        totals["period_start"] = totals["period_start"].isoformat()
    if totals["period_end"]:
        totals["period_end"] = totals["period_end"].isoformat()

    totals["savings_simulated"] = round(0.005 * totals["total_value_sum"], 2)
    return totals

# ===========================
# 📂 1. Rodar análise a partir de arquivo salvo no disco
# ===========================
def run_analysis_for_upload(storage_key: str) -> Dict[str, Any]:
    path = get_zip_path(storage_key)
    with zipfile.ZipFile(path, "r") as zf:
        return _run_analysis_from_zipfile(zf)

# ===========================
# 🧠 2. Rodar análise a partir de bytes em memória
# ===========================
def run_analysis_from_bytes(zip_bytes: bytes) -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return _run_analysis_from_zipfile(zf)
