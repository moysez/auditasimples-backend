from lxml import etree
from datetime import datetime

def parse_nfe_xml(xml_bytes: bytes) -> dict:
    """
    Faz o parse de um XML de NF-e ou SAT e retorna dados padronizados.
    """
    root = etree.fromstring(xml_bytes)
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    total_value = 0.0
    issue_date = None
    items = []

    # Data de emissão
    ide = root.find(".//nfe:ide", namespaces=ns)
    if ide is not None:
        dhEmi = ide.findtext("nfe:dhEmi", namespaces=ns)
        if dhEmi:
            issue_date = datetime.fromisoformat(dhEmi.replace("Z", "+00:00"))

    # Itens da nota
    for det in root.findall(".//nfe:det", namespaces=ns):
        prod = det.find(".//nfe:prod", namespaces=ns)
        if prod is not None:
            xProd = prod.findtext("nfe:xProd", namespaces=ns)
            ncm = prod.findtext("nfe:NCM", namespaces=ns)
            cfop = prod.findtext("nfe:CFOP", namespaces=ns)
            vProd = prod.findtext("nfe:vProd", namespaces=ns)
            csosn = prod.findtext("nfe:CSOSN", namespaces=ns)

            items.append({
                "xProd": xProd or "",
                "ncm": ncm or "",
                "cfop": cfop or "",
                "csosn": csosn or "",
                "vProd": float(vProd or 0)
            })
            total_value += float(vProd or 0)

    return {
        "total_value": total_value,
        "issue_date": issue_date,
        "items": items
    }
