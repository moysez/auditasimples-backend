from __future__ import annotations
from typing import Dict, Any
import io
import zipfile
from datetime import datetime
from .nfe import parse_nfe_xml
from .ai_matcher import matcher

def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

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

        # 📊 Resultado tributário
        'tax_summary': {}
    }

def run_analysis_from_bytes(zip_bytes: bytes, aliquota: float = None, imposto_pago: float = None) -> Dict[str, Any]:
    totals = init_totals()

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
                desc = item.get('xProd', '')
                ncm = item.get('ncm', '')
                cfop = item.get('cfop', '')
                csosn = item.get('csosn', '')
                vprod = float(item.get('vProd', 0) or 0)

                # 👀 Detectar monofásico
                is_mono = False
                hit = matcher.classify(desc)
                if hit and matcher.is_monofasico(hit[0]):
                    is_mono = True
                    totals['monofasico_palavra_chave'] += 1
                    if not _has_valid_ncm(ncm):
                        totals['monofasico_sem_ncm'] += 1

                # ✅ Tributação correta (não gera economia)
                if is_mono and cfop == "5405" and csosn == "500":
                    totals['st_cfop_csosn_corretos'] += 1
                    totals['st_correct_items_value'] += vprod
                    continue  # não soma em receita excluída

                # ❌ Tributação incorreta → soma para base de economia
                if is_mono:
                    key = hit[0] if hit else "unknown"
                    totals['revenue_excluded_breakdown'].setdefault(key, 0.0)
                    totals['revenue_excluded_breakdown'][key] += vprod
                    totals['revenue_excluded'] += vprod

                # 🚨 Verifica NCM vs categoria
                if hit:
                    val = matcher.validate_ncm_for_category(ncm, hit[0])
                    if not val["ncm_valido"]:
                        totals['erros_ncm_categoria'] += 1

                # 🚨 Conta ST incorreto
                if not (cfop == "5405" and csosn == "500"):
                    totals['st_incorreta'] += 1

    # 🕒 Converter datas
    if totals['period_start']:
        totals['period_start'] = totals['period_start'].isoformat()
    if totals['period_end']:
        totals['period_end'] = totals['period_end'].isoformat()

    # 💰 Cálculo tributário
    faturamento = totals['total_value_sum']
    receita_excluida = totals['revenue_excluded']
    base_corrigida = faturamento - receita_excluida

    imposto_corrigido = None
    economia_estimada = None

    if aliquota is not None:
        imposto_base_atual = faturamento * aliquota
        imposto_corrigido = base_corrigida * aliquota
        economia_estimada = max(0, imposto_base_atual - imposto_corrigido)
    elif imposto_pago is not None:
        try:
            aliquota_media = imposto_pago / faturamento if faturamento > 0 else 0
            imposto_corrigido = base_corrigida * aliquota_media
            economia_estimada = max(0, imposto_pago - imposto_corrigido)
        except Exception:
            economia_estimada = None

    totals['tax_summary'] = {
        'faturamento': faturamento,
        'base_corrigida': base_corrigida,
        'receita_excluida': receita_excluida,
        'imposto_corrigido': imposto_corrigido,
        'economia_estimada': economia_estimada,
        'aliquota_utilizada': aliquota if aliquota is not None else (imposto_pago / faturamento if faturamento else 0),
        'imposto_pago_informado': imposto_pago,
    }

    return totals
