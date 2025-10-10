import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List


def parse_nfe_xml(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Faz o parse de um XML de NF-e e retorna dados essenciais para análise.
    Retorna:
        - total_value: float (valor total da nota)
        - issue_date: datetime (data de emissão)
        - items: lista de produtos com xProd, ncm, cfop, csosn
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        # se o XML estiver corrompido ou inválido
        return {"total_value": 0.0, "issue_date": None, "items": []}

    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    # 📌 Total da nota (ICMSTot/vNF)
    total_value = 0.0
    vnf_el = root.find(".//nfe:ICMSTot/nfe:vNF", ns)
    if vnf_el is not None and vnf_el.text:
        try:
            total_value = float(vnf_el.text.replace(",", "."))
        except ValueError:
            total_value = 0.0

    # 🗓️ Data de emissão (ide/dhEmi ou ide/dEmi)
    issue_date = None
    dh_emi_el = root.find(".//nfe:ide/nfe:dhEmi", ns) or root.find(".//nfe:ide/nfe:dEmi", ns)
    if dh_emi_el is not None and dh_emi_el.text:
        try:
            issue_date = datetime.fromisoformat(dh_emi_el.text.replace("Z", "+00:00"))
        except Exception:
            try:
                issue_date = datetime.strptime(dh_emi_el.text, "%Y-%m-%d")
            except Exception:
                issue_date = None

    # 🧾 Itens da nota (det/prod)
    items: List[Dict[str, Any]] = []
    for det in root.findall(".//nfe:det", ns):
        prod_el = det.find("./nfe:prod", ns)
        if prod_el is None:
            continue

        xProd = prod_el.findtext("nfe:xProd", default="", namespaces=ns)
        ncm = prod_el.findtext("nfe:NCM", default="", namespaces=ns)
        cfop = prod_el.findtext("nfe:CFOP", default="", namespaces=ns)

        # CSOSN pode estar dentro de imposto/ICMS/ICMSSN*
        csosn = ""
        icms = det.find(".//nfe:ICMS", ns)
        if icms is not None:
            for csosn_tag in ["ICMSSN101", "ICMSSN102", "ICMSSN103", "ICMSSN201", "ICMSSN202", "ICMSSN500"]:
                csosn_el = icms.find(f".//nfe:{csosn_tag}/nfe:CSOSN", ns)
                if csosn_el is not None and csosn_el.text:
                    csosn = csosn_el.text
                    break

        items.append({
            "xProd": xProd.strip(),
            "ncm": ncm.strip(),
            "cfop": cfop.strip(),
            "csosn": csosn.strip(),
        })

    return {
        "total_value": total_value,
        "issue_date": issue_date,
        "items": items
    }
