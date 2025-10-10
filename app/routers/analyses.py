from __future__ import annotations
from typing import Dict, Any
import zipfile
from .nfe import parse_nfe_xml
from ..services.storage import get_zip_path

# 🧾 Palavras-chave para identificar produtos monofásicos
KEYWORDS_MONO = [
    'refrigerante', 'coca', 'coca-cola', 'cerveja', 'skol', 'brahma', 'antarctica',
    'guaraná', 'guarana', 'pepsi', 'heineken', 'amstel'
]

def _is_monofasico_by_desc(desc: str) -> bool:
    """
    Verifica se a descrição do produto contém palavras-chave de produtos monofásicos.
    """
    d = (desc or '').lower()
    return any(k in d for k in KEYWORDS_MONO)

def _has_valid_ncm(ncm: str) -> bool:
    """
    Verifica se o NCM informado tem 8 dígitos numéricos.
    """
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

def run_analysis_for_upload(storage_key: str) -> Dict[str, Any]:
    """
    Processa o arquivo ZIP de XMLs fiscais e retorna um resumo analítico:
    - Total de documentos e itens
    - Período inicial e final das notas
    - Detecção de monofásicos
    - Erros fiscais (sem NCM / CFOP-CSOSN incorretos)
    - Simulação de economia tributária
    """
    path = get_zip_path(storage_key)
    totals = {
        'documents': 0,
        'total_value_sum': 0.0,
        'period_start': None,
        'period_end': None,
        'items': 0,
        'monofasico_sem_ncm': 0,
        'monofasico_palavra_chave': 0,
        'st_cfop_csosn_corretos': 0,
        'st_incorreta': 0,
    }

    try:
        with zipfile.ZipFile(path, 'r') as zf:
            for name in zf.namelist():
                if not name.lower().endswith('.xml'):
                    continue

                try:
                    xml_bytes = zf.read(name)
                except Exception:
                    # Se não conseguir ler, ignora o arquivo
                    continue

                # Parse do XML em dicionário padronizado
                try:
                    doc = parse_nfe_xml(xml_bytes)
                except Exception:
                    # Se o XML estiver corrompido ou inválido
                    continue

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

                    # Produtos monofásicos detectados por palavra-chave
                    if _is_monofasico_by_desc(desc):
                        totals['monofasico_palavra_chave'] += 1
                        if not _has_valid_ncm(ncm):
                            totals['monofasico_sem_ncm'] += 1

                    # Verifica CFOP e CSOSN corretos para ST
                    if cfop == '5405' and csosn == '500':
                        totals['st_cfop_csosn_corretos'] += 1
                    else:
                        totals['st_incorreta'] += 1

    except zipfile.BadZipFile:
        raise ValueError("Arquivo ZIP inválido ou corrompido.")

    # Converte datas para ISO
    if totals['period_start']:
        totals['period_start'] = totals['period_start'].isoformat()
    if totals['period_end']:
        totals['period_end'] = totals['period_end'].isoformat()

    # Simula economia fiscal (exemplo: 0,5% sobre o valor total)
    totals['savings_simulated'] = round(0.005 * totals['total_value_sum'], 2)

    return totals
