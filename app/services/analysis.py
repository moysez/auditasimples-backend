from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
import io
import zipfile
import logging
from collections import defaultdict

from .nfe import parse_nfe_xml
from .ai_matcher import matcher

logger = logging.getLogger(__name__)

# -------------------------------------------------
# 🛡️ Funções auxiliares
# -------------------------------------------------
def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

def _parse_float_safe(value) -> float:
    """Normaliza string com vírgula/ponto para float seguro."""
    if isinstance(value, str):
        value = value.replace('.', '').replace(',', '.')
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def _parse_percentish(value) -> float:
    """
    Aceita 0.08, '0,08', 8, '8', '8%', etc. Retorna fração (0.08).
    """
    if value is None:
        return 0.0
    if isinstance(value, str):
        v = value.strip().replace('%', '')
        v = _parse_float_safe(v)
    else:
        v = float(value)
    if v > 1.0:  # veio como 8 → 8%
        v = v / 100.0
    if v < 0.0:
        v = 0.0
    return v

def _safe_float(value):
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

    # coletores para o relatório
    produtos_raw = []                 # lista completa de itens monofásicos
    dedup_map: Dict[str, dict] = {}   # deduplicados — apenas monofásicos
    dedup_code_count = defaultdict(lambda: defaultdict(int))  # desc → código → contagem
    excluidos = []                    # produtos monofásicos tributados incorretamente

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
                codigo = (item.get('cProd') or '')
                qnt = item.get('qCom')
                vun = item.get('vUnCom')
                vprod = _parse_float_safe(item.get('vProd') or 0)

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

                # 🚨 Verifica NCM vs categoria
                if hit:
                    val = matcher.validate_ncm_for_category(ncm, hit[0])
                    if not val["ncm_valido"]:
                        totals['erros_ncm_categoria'] += 1

                # 🧾 Salva produto bruto (somente monofásico para o relatório)
                if is_mono:
                    produtos_raw.append({
                        "descricao": desc,
                        "ncm": ncm,
                        "cfop": cfop,
                        "csosn": csosn,
                        "valor_total": vprod,
                        "valor_unitario": vun,
                        "quantidade": qnt,
                        "codigo": codigo,
                        "numero": doc.get('numero'),
                        "data_emissao": dt.isoformat() if dt else None,
                        "chave": doc.get('chave'),
                        "monofasico": True,
                        "st_correto": (cfop == "5405" and csosn == "500")
                    })

                    # 📊 Deduplicação — apenas monofásicos
                    key_desc = desc.lower()
                    if key_desc not in dedup_map:
                        dedup_map[key_desc] = {
                            "descricao": desc,
                            "ocorrencias": 1,
                            "valor_total": vprod,
                            "codigo": codigo or ""
                        }
                    else:
                        d = dedup_map[key_desc]
                        d["ocorrencias"] += 1
                        d["valor_total"] += vprod
                    if codigo:
                        dedup_code_count[key_desc][codigo] += 1

                    # 🪙 Lista de excluídos (monofásicos tributados incorretamente)
                    if not (cfop == "5405" and csosn == "500"):
                        excluidos.append({
                            "descricao": desc,
                            "valor_total": vprod,
                            "ncm": ncm,
                            "cfop": cfop,
                            "csosn": csosn,
                            "codigo": codigo,
                            "quantidade": qnt,
                            "valor_unitario": vun,
                            "numero": doc.get('numero'),
                            "data_emissao": dt.isoformat() if dt else None,
                            "chave": doc.get('chave')
                        })

    # Após varredura: fixa o código mais frequente por descrição nos deduplicados
    for key_desc, d in dedup_map.items():
        counts = dedup_code_count.get(key_desc, {})
        if counts:
            d["codigo"] = max(counts.items(), key=lambda kv: kv[1])[0]

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
    # Normalizações de entrada
    if imposto_pago is not None:
        imposto_pago = _parse_float_safe(imposto_pago)
    aliquota_frac = 0.0
    if aliquota is not None:
        aliquota_frac = _parse_percentish(aliquota)

    faturamento = totals['total_value_sum']
    receita_excluida = totals['revenue_excluded']
    base_corrigida = faturamento - receita_excluida

    imposto_corrigido = 0.0
    economia_estimada = 0.0
    imposto_pago_final = 0.0

    try:
        if aliquota is not None:  # usuário forneceu alíquota
            imposto_base_atual = faturamento * aliquota_frac
            imposto_corrigido = base_corrigida * aliquota_frac
            economia_estimada = max(0, imposto_base_atual - imposto_corrigido)
            imposto_pago_final = imposto_base_atual
        elif imposto_pago is not None:
            aliquota_media = (imposto_pago / faturamento) if faturamento > 0 else 0.0
            imposto_corrigido = base_corrigida * aliquota_media
            economia_estimada = max(0, imposto_pago - imposto_corrigido)
            imposto_pago_final = imposto_pago
        else:
            # sem parâmetros → tudo zero
            imposto_corrigido = 0.0
            economia_estimada = 0.0
            imposto_pago_final = 0.0
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
        'aliquota_utilizada': (
            aliquota_frac
            if aliquota is not None
            else (
                (imposto_pago / faturamento)
                if (imposto_pago is not None and faturamento)
                else 0.0
            )
        ),
        'imposto_pago': imposto_pago_final,
        'imposto_pago_informado': imposto_pago
    }

    for k, v in tax_summary.items():
        tax_summary[k] = _safe_float(v)

    totals['tax_summary'] = tax_summary
    totals['products'] = produtos_raw
    totals['produtos_duplicados'] = sorted(dedup_map.values(), key=lambda x: x["valor_total"], reverse=True)
    totals['produtos_excluidos'] = excluidos

    logger.info(f"[DEBUG ANALYSIS] tax_summary final: {tax_summary}")
    logger.info(
        "[DEBUG ANALYSIS] Monofásicos totais: %s / ST incorretos: %s / sem CFOP/CSOSN: %s",
        totals['monofasico_total'], totals['st_incorreta'], totals['monofasico_sem_cfop_csosn']
    )

    return totals
