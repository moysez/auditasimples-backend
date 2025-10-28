from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
import io
import zipfile
import logging

from .nfe import parse_nfe_xml
from .ai_matcher import matcher

logger = logging.getLogger(__name__)

# -------------------------------------------------
# 🛡️ Funções auxiliares
# -------------------------------------------------
def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

def parse_float_safe(value) -> float:
    """Normaliza string com vírgula/ponto para float seguro."""
    if isinstance(value, str):
        value = value.replace('.', '').replace(',', '.')
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def init_totals() -> dict:
    return {
        # 📊 Documentos e valores
        'documents': 0,
        'total_value_sum': 0.0,
        'period_start': None,
        'period_end': None,
        'items': 0,

        # 💰 Receita monofásica a excluir
        'revenue_excluded': 0.0,
        'revenue_excluded_breakdown': {},
        'st_correct_items_value': 0.0,

        # 🧾 Indicadores fiscais
        'monofasico_palavra_chave': 0,
        'monofasico_sem_ncm': 0,
        'st_cfop_csosn_corretos': 0,
        'st_incorreta': 0,
        'erros_ncm_categoria': 0,
        'erros_outros': 0,

        # 📊 Contadores auxiliares
        'monofasico_total': 0,
        'monofasico_sem_cfop_csosn': 0,

        # 📊 Resultado tributário
        'tax_summary': {}
    }

# -------------------------------------------------
# 🧠 Função principal
# -------------------------------------------------
def run_analysis_from_bytes(zip_bytes: bytes, aliquota: float = None, imposto_pago: float = None) -> Dict[str, Any]:
    totals = init_totals()
    produtos_raw = []   # lista de itens monofásicos
    dedup_map = {}      # deduplicação — apenas monofásicos
    excluidos = []      # monofásicos tributados incorretamente

    # ======================================================
    # 📦 Leitura única dos XMLs
    # ======================================================
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        for name in zf.namelist():
            if not name.lower().endswith('.xml'):
                continue

            xml_bytes = zf.read(name)
            doc = parse_nfe_xml(xml_bytes)
            totals['documents'] += 1
            totals['total_value_sum'] += doc.get('total_value', 0.0)

            dt = doc.get('issue_date')
            if dt:
                if totals['period_start'] is None or dt < totals['period_start']:
                    totals['period_start'] = dt
                if totals['period_end'] is None or dt > totals['period_end']:
                    totals['period_end'] = dt

            for item in doc.get('items', []):
                totals['items'] += 1
                desc = (item.get('xProd') or '').strip()
                ncm = (item.get('ncm') or '').strip()
                cfop = (item.get('cfop') or '').strip()
                csosn = (item.get('csosn') or '').strip()
                vprod = float(item.get('vProd') or 0)

                # 👀 IA: Detectar monofásico
                is_mono = False
                hit = matcher.classify(desc)
                if hit and matcher.is_monofasico(hit[0]):
                    is_mono = True
                    totals['monofasico_palavra_chave'] += 1
                    totals['monofasico_total'] += 1
                    if not _has_valid_ncm(ncm):
                        totals['monofasico_sem_ncm'] += 1
                    if not (cfop and csosn):
                        totals['monofasico_sem_cfop_csosn'] += 1

                # ✅ ST Correto
                if is_mono and cfop == "5405" and csosn == "500":
                    totals['st_cfop_csosn_corretos'] += 1
                    totals['st_correct_items_value'] += vprod
                # ❌ ST Incorreto
                elif is_mono:
                    key = hit[0] if hit else "unknown"
                    totals['revenue_excluded_breakdown'].setdefault(key, 0.0)
                    totals['revenue_excluded_breakdown'][key] += vprod
                    totals['revenue_excluded'] += vprod
                    totals['st_incorreta'] += 1

                # 🚨 Validação NCM vs categoria
                if hit:
                    val = matcher.validate_ncm_for_category(ncm, hit[0])
                    if not val["ncm_valido"]:
                        totals['erros_ncm_categoria'] += 1

                # 🧾 Somente monofásicos seguem para o relatório
                if is_mono:
                    codigo = item.get('cProd')
                    v_un = item.get('vUnCom')
                    q_com = item.get('qCom')

                    produtos_raw.append({
                        "descricao": desc,
                        "ncm": ncm,
                        "cfop": cfop,
                        "csosn": csosn,
                        "valor_total": vprod,
                        "valor_unitario": v_un,
                        "quantidade": q_com,
                        "codigo": codigo,
                        "numero": doc.get('numero'),
                        "data_emissao": dt.isoformat() if dt else None,
                        "chave": doc.get('chave'),
                        "monofasico": True,
                        "st_correto": (cfop == "5405" and csosn == "500")
                    })

                    # 📊 Deduplicação (somente monofásicos) — mantém 1 código representativo
                    key = (codigo or '').strip() + '|' + desc.lower()
                    if key not in dedup_map:
                        dedup_map[key] = {
                            "codigo": codigo or "",
                            "descricao": desc,
                            "ocorrencias": 1,
                            "valor_total": vprod,
                        }
                    else:
                        dedup_map[key]["ocorrencias"] += 1
                        dedup_map[key]["valor_total"] += vprod

                    # 🪙 Lista de excluídos (monofásicos tributados incorretamente)
                    if not (cfop == "5405" and csosn == "500"):
                        excluidos.append({
                            "descricao": desc,
                            "valor_total": vprod,
                            "ncm": ncm,
                            "cfop": cfop,
                            "csosn": csosn,
                            "codigo": codigo,
                            "quantidade": q_com,
                            "valor_unitario": v_un,
                            "numero": doc.get('numero'),
                            "data_emissao": dt.isoformat() if dt else None,
                            "chave": doc.get('chave')
                        })

    # ======================================================
    # 🕒 Converter datas
    # ======================================================
    if totals['period_start']:
        totals['period_start'] = totals['period_start'].isoformat()
    if totals['period_end']:
        totals['period_end'] = totals['period_end'].isoformat()

    # ======================================================
    # 💰 Cálculo tributário
    # ======================================================
    # Normaliza imposto_pago informado (pode vir "100x" por erro de formatação)
    if imposto_pago is not None:
        imposto_pago = parse_float_safe(imposto_pago)

    faturamento = totals['total_value_sum']
    receita_excluida = totals['revenue_excluded']
    base_corrigida = faturamento - receita_excluida

    imposto_corrigido = 0.0
    economia_estimada = 0.0
    imposto_pago_final = 0.0
    aliquota_usada = 0.0

    try:
        if aliquota is not None:
            # Se vier em % (ex.: 10), converte para fração (0.10)
            aliquota_usada = float(aliquota)
            if aliquota_usada > 1.0:
                aliquota_usada = aliquota_usada / 100.0

            imposto_base_atual = faturamento * aliquota_usada
            imposto_corrigido = base_corrigida * aliquota_usada
            economia_estimada = max(0.0, imposto_base_atual - imposto_corrigido)
            imposto_pago_final = imposto_base_atual

        elif imposto_pago is not None:
            imposto_pago_final = float(imposto_pago)
            if faturamento > 0:
                aliquota_media = imposto_pago_final / faturamento  # fração esperada (ex.: 0.10)
                # Defesa: se por erro vier >= 1 (ex.: 10.0), corrige para fração
                if aliquota_media > 1.0:
                    aliquota_media = aliquota_media / 100.0
                aliquota_usada = aliquota_media
                imposto_corrigido = base_corrigida * aliquota_media
                economia_estimada = max(0.0, imposto_pago_final - imposto_corrigido)
    except Exception as e:
        logger.warning(f"[ANÁLISE] Falha no cálculo tributário: {e}")
        economia_estimada = 0.0
        imposto_corrigido = 0.0

    # ======================================================
    # 🧼 Sanitizar tax_summary
    # ======================================================
    tax_summary = {
        'faturamento': faturamento,
        'base_corrigida': base_corrigida,
        'receita_excluida': receita_excluida,
        'imposto_corrigido': imposto_corrigido,
        'economia_estimada': economia_estimada,
        'aliquota_utilizada': aliquota_usada,
        'imposto_pago': imposto_pago_final,
        'imposto_pago_informado': imposto_pago
    }

    for k, v in tax_summary.items():
        tax_summary[k] = safe_float(v)

    totals['tax_summary'] = tax_summary
    totals['products'] = produtos_raw
    # agora cada chave é "codigo|descricao" garantindo a coluna Código no relatório
    totals['produtos_duplicados'] = sorted(
        [{"codigo": v["codigo"], "descricao": v["descricao"], "ocorrencias": v["ocorrencias"], "valor_total": v["valor_total"]}
         for v in dedup_map.values()],
        key=lambda x: x["valor_total"],
        reverse=True
    )
    totals['produtos_excluidos'] = excluidos

    logger.info(f"[DEBUG ANALYSIS] tax_summary final: {tax_summary}")
    logger.info(f"[DEBUG ANALYSIS] Monofásicos totais: {totals['monofasico_total']} / ST incorretos: {totals['st_incorreta']} / sem CFOP/CSOSN: {totals['monofasico_sem_cfop_csosn']}")

    return totals
