# app/services/nfe.py
from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

def _txt(node: Optional[ET.Element]) -> str:
    return (node.text or "").strip() if node is not None and node.text else ""

def _nsroot(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    # Detecta namespace dinamicamente (NFe 3.10, 4.00, etc.)
    if "}" in root.tag:
        ns_uri = root.tag.split("}")[0].strip("{")
        ns = {"nfe": ns_uri}
    else:
        ns = {"nfe": ""}  # sem namespace
    return root, ns

def _find(root: ET.Element, path: str, ns: Dict[str,str]) -> Optional[ET.Element]:
    return root.find(path, ns) if ns.get("nfe") else root.find(path.replace("nfe:", ""))

def _findall(root: ET.Element, path: str, ns: Dict[str,str]) -> List[ET.Element]:
    return root.findall(path, ns) if ns.get("nfe") else root.findall(path.replace("nfe:", ""))

def parse_nfe_xml(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Retorna um dicionário padrão consumido por analysis.py com:
      - issue_date (datetime)
      - total_value (float)
      - cNF (número do documento)
      - chNFe (chave da NFe – preferindo a do protocolo, senão 'Id' do infNFe)
      - items[]: cProd, xProd, NCM, CFOP, qCom, vUnCom, vProd, CSOSN/CST
    """
    root, ns = _nsroot(xml_bytes)

    # ============== Cabeçalho / Datas ==============
    issue_date = None
    dhEmi = _find(root, ".//nfe:ide/nfe:dhEmi", ns)
    dEmi  = _find(root, ".//nfe:ide/nfe:dEmi", ns)
    raw_dt = _txt(dhEmi) or _txt(dEmi)
    if raw_dt:
        # Tenta vários formatos comuns
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                issue_date = datetime.strptime(raw_dt, fmt)
                break
            except Exception:
                continue

    # Número (cNF)
    cNF = _txt(_find(root, ".//nfe:ide/nfe:cNF", ns))

    # Chave da NFe
    # 1) Preferir protocolo (mais confiável quando existe)
    chNFe = _txt(_find(root, ".//nfe:protNFe/nfe:infProt/nfe:chNFe", ns))
    if not chNFe:
        # 2) Usar atributo Id do infNFe (vem como 'NFe<chave>')
        infNFe = _find(root, ".//nfe:infNFe", ns)
        if infNFe is not None:
            chNFe = (infNFe.attrib.get("Id", "") or "").replace("NFe", "").strip()

    # Valor total da nota (vNF)
    vNF = _txt(_find(root, ".//nfe:ICMSTot/nfe:vNF", ns))
    try:
        total_value = float(vNF.replace(",", ".")) if vNF else 0.0
    except Exception:
        total_value = 0.0

    # ============== Itens ==============
    items: List[Dict[str, Any]] = []
    for det in _findall(root, ".//nfe:det", ns):
        prod = _find(det, "./nfe:prod", ns)
        imposto = _find(det, "./nfe:imposto", ns)

        cProd  = _txt(_find(prod, "nfe:cProd", ns)) if prod is not None else ""
        xProd  = _txt(_find(prod, "nfe:xProd", ns)) if prod is not None else ""
        NCM    = _txt(_find(prod, "nfe:NCM", ns)) if prod is not None else ""
        CFOP   = _txt(_find(prod, "nfe:CFOP", ns)) if prod is not None else ""
        qCom   = _txt(_find(prod, "nfe:qCom", ns)) if prod is not None else "0"
        vUnCom = _txt(_find(prod, "nfe:vUnCom", ns)) if prod is not None else "0"
        vProd  = _txt(_find(prod, "nfe:vProd", ns)) if prod is not None else "0"

        # Converte números com vírgula para float/str coerente
        try:
            vProd_f = float(vProd.replace(",", ".")) if vProd else 0.0
        except Exception:
            vProd_f = 0.0

        # CSOSN/CST (pode estar em diferentes nós sob ICMS)
        csosn = ""
        if imposto is not None:
            icms = _find(det, ".//nfe:ICMS", ns)
            if icms is not None:
                # Busca CSOSN em qualquer subnó de ICMS (ex.: ICMSSN102, ICMSSN500…)
                csosn_node = None
                for child in list(icms):
                    csosn_node = _find(child, "nfe:CSOSN", ns)
                    if csosn_node is not None and _txt(csosn_node):
                        break
                    # Em alguns casos só há CST
                    if csosn_node is None:
                        csosn_node = _find(child, "nfe:CST", ns)
                        if csosn_node is not None and _txt(csosn_node):
                            break
                csosn = _txt(csosn_node) if csosn_node is not None else ""

        items.append({
            "cProd": cProd,
            "xProd": xProd,
            "ncm": NCM,
            "cfop": CFOP,
            "qCom": qCom,
            "vUnCom": vUnCom,
            "vProd": vProd_f,
            "csosn": csosn
        })

    print("✅ parse_nfe_xml carregado de app/services/nfe.py")
    return {
        "issue_date": issue_date,
        "total_value": total_value,
        "cNF": cNF,
        "chNFe": chNFe,
        "items": items
    }
