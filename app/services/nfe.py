from __future__ import annotations
from typing import Dict, List, Any
from datetime import datetime
import xml.etree.ElementTree as ET

def _text(node):
    return node.text.strip() if node is not None and node.text else ''

def parse_nfe_xml(xml_bytes):
    root = ET.fromstring(xml_bytes)

    # 📌 Detecta automaticamente o namespace (prefixo dinâmico)
    if "}" in root.tag:
        ns_uri = root.tag.split("}")[0].strip("{")
        ns = {"ns": ns_uri}
    else:
        ns = {}

    # 🧾 Data de emissão
    issue_date = None
    dt_node = root.find(".//ns:ide/ns:dhEmi", ns)
    if dt_node is None:
        dt_node = root.find(".//ns:ide/ns:dEmi", ns)
    if dt_node is not None and _text(dt_node):
        raw = _text(dt_node)
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                issue_date = datetime.strptime(raw, fmt)
                break
            except Exception:
                pass

    # 💰 Valor total da nota
    vnf_node = root.find(".//ns:ICMSTot/ns:vNF", ns)
    total_value = 0.0
    if vnf_node is not None and _text(vnf_node):
        try:
            total_value = float(_text(vnf_node).replace(",", "."))
        except ValueError:
            total_value = 0.0

    # 📦 Itens
    items: List[Dict[str, Any]] = []
    for det in root.findall(".//ns:det", ns):
        prod = det.find("./ns:prod", ns)
        imposto = det.find("./ns:imposto", ns)

        xProd = _text(prod.find("ns:xProd", ns)) if prod is not None else ""
        ncm = _text(prod.find("ns:NCM", ns)) if prod is not None else ""
        cfop = _text(prod.find("ns:CFOP", ns)) if prod is not None else ""
        vProd = _text(prod.find("ns:vProd", ns)) if prod is not None else "0"
        try:
            vProd = float(vProd.replace(",", "."))
        except Exception:
            vProd = 0.0

        csosn = ""
        if imposto is not None:
            # Tenta pegar CSOSN ou CST
            for icms in imposto.findall(".//ns:ICMS", ns):
                cand = icms.find("ns:CSOSN", ns)
                if cand is None:
                    cand = icms.find("ns:CST", ns)
                if cand is not None and _text(cand):
                    csosn = _text(cand)
                    break

        items.append({
            "xProd": xProd,
            "ncm": ncm,
            "cfop": cfop,
            "csosn": csosn,
            "vProd": vProd
        })

    print("✅ parse_nfe_xml carregado de app/services/nfe.py")
    return {"issue_date": issue_date, "total_value": total_value, "items": items}
