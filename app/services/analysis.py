import io
import zipfile
from typing import Dict, Any
from .nfe import parse_nfe_xml
from .ia import classify_product  # 👈 nova função IA que vamos criar

KEYWORDS_MONO = [
    'refrigerante','coca','coca-cola','cerveja','skol','brahma','antarctica',
    'guaraná','guarana','pepsi','heineken','amstel'
]

def _is_monofasico_by_desc(desc: str) -> bool:
    return any(k in (desc or '').lower() for k in KEYWORDS_MONO)

def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

def run_analysis_from_bytes(zip_bytes: bytes) -> Dict[str, Any]:
    totals = {
        'documents': 0, 'total_value_sum': 0.0,
        'period_start': None, 'period_end': None,
        'items': 0,
        'monofasico_sem_ncm': 0, 'monofasico_palavra_chave': 0,
        'monofasico_ia_detectado': 0,  # 👈 novo
        'st_cfop_csosn_corretos': 0, 'st_incorreta': 0,
    }

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
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
                desc = item.get('xProd', ''); ncm = item.get('ncm', '')
                cfop = item.get('cfop', ''); csosn = item.get('csosn', '')

                # 1️⃣ Palavras-chave
                if _is_monofasico_by_desc(desc):
                    totals['monofasico_palavra_chave'] += 1
                    if not _has_valid_ncm(ncm):
                        totals['monofasico_sem_ncm'] += 1

                # 2️⃣ Classificação com IA
                if classify_product(desc):  # 👈 chama IA
                    totals['monofasico_ia_detectado'] += 1
                    if not _has_valid_ncm(ncm):
                        totals['monofasico_sem_ncm'] += 1

                # 3️⃣ Verificação de ST
                if cfop == '5405' and csosn == '500':
                    totals['st_cfop_csosn_corretos'] += 1
                else:
                    totals['st_incorreta'] += 1

    if totals['period_start']:
        totals['period_start'] = totals['period_start'].isoformat()
    if totals['period_end']:
        totals['period_end'] = totals['period_end'].isoformat()

    totals['savings_simulated'] = round(0.005 * totals['total_value_sum'], 2)
    return totals
