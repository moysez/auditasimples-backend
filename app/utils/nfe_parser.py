from lxml import etree

def _text(el, xp):
    r = el.xpath(xp)
    if not r: return ""
    if isinstance(r, list): r = r[0]
    if hasattr(r, 'text'): return (r.text or "").strip()
    return (str(r) or "").strip()

def parse_xml_for_basic_fields(xml_bytes: bytes):
    root = etree.fromstring(xml_bytes)
    nsmap = root.nsmap.copy()
    if None in nsmap: nsmap["nfe"] = nsmap.pop(None)
    chave = _text(root, "//nfe:infNFe/@Id") or _text(root, "//infNFe/@Id")
    cfop  = _text(root, "//nfe:det/nfe:prod/nfe:CFOP") or _text(root, "//det/prod/CFOP")
    ncm   = _text(root, "//nfe:det/nfe:prod/nfe:NCM") or _text(root, "//det/prod/NCM")
    cst   = _text(root, "//nfe:det/nfe:imposto//nfe:CST") or _text(root, "//det/imposto//CST")
    return { "chave": chave.replace("NFe", "").strip("-"), "cfop": cfop, "ncm": ncm, "cst": cst }
