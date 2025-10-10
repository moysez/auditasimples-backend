from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime
from lxml import etree

NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

def _text(node):
    return node.text.strip() if node is not None and node.text else ''

def parse_nfe_xml(xml_bytes: bytes) -> Dict[str, Any]:
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        xml_bytes = xml_bytes.strip()
        root = etree.fromstring(xml_bytes)

    nfe = root.find('.//nfe:NFe', namespaces=NS)
    if nfe is None:
        nfe = root

    dt = nfe.find('.//nfe:ide/nfe:dhEmi', namespaces=NS)
    if dt is None:
        dt = nfe.find('.//nfe:ide/nfe:dEmi', namespaces=NS)

    issue_date = None
    if dt is not None and _text(dt):
        raw = _text(dt)
        for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
            try:
                issue_date = datetime.strptime(raw, fmt)
                break
            except Exception:
                pass

    vnf_node = nfe.find('.\nfe:total//nfe:ICMSTot/nfe:vNF', namespaces=NS)
    if vnf_node is None:
        vnf_node = nfe.find('.//nfe:total//nfe:ICMSTot/nfe:vNF', namespaces=NS)
    total_value = float(_text(vnf_node).replace(',', '.')) if vnf_node is not None and _text(vnf_node) else 0.0

    items: List[Dict[str, Any]] = []
    for det in nfe.findall('.//nfe:det', namespaces=NS):
        prod = det.find('nfe:prod', namespaces=NS)
        imposto = det.find('nfe:imposto', namespaces=NS)

        xProd = _text(prod.find('nfe:xProd', namespaces=NS)) if prod is not None else ''
        ncm = _text(prod.find('nfe:NCM', namespaces=NS)) if prod is not None else ''
        cfop = _text(prod.find('nfe:CFOP', namespaces=NS)) if prod is not None else ''
        vProd = _text(prod.find('nfe:vProd', namespaces=NS)) if prod is not None else '0'
        try:
            vProd = float(vProd.replace(',', '.'))
        except Exception:
            vProd = 0.0

        csosn = ''
        if imposto is not None:
            for icms in imposto.findall('.//nfe:ICMS*', namespaces=NS):
                cand = icms.find('nfe:CSOSN', namespaces=NS)
                if cand is None:
                    cand = icms.find('nfe:CST', namespaces=NS)
                if cand is not None and _text(cand):
                    csosn = _text(cand)
                    break

        items.append({'xProd': xProd, 'ncm': ncm, 'cfop': cfop, 'csosn': csosn, 'vProd': vProd})

    return {'issue_date': issue_date, 'total_value': total_value, 'items': items}
