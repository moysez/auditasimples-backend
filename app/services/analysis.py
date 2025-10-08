import io, zipfile
from sqlalchemy.orm import Session
from ..models import Upload, AnalysisJob, Report
from .storage import get_zip_bytes
from ..utils.nfe_parser import parse_xml_for_basic_fields

MONOFASICOS_NCM = {"2401", "2402", "2403"}
ST_NCM = {"2203", "3303"}

def apply_rules(entries):
    findings = []
    totals = {"docs": 0, "suspeitas": 0}
    for e in entries:
        issue_list = []
        ncm = e.get("ncm") or ""
        if len(ncm) < 4:
            issue_list.append({"code": "NCM_MISSING", "msg": "NCM ausente ou inválido"})
        if ncm[:4] in MONOFASICOS_NCM and e.get("cst") not in {"04", "06"}:
            issue_list.append({"code": "CST_MONO", "msg": "CST incompatível com monofásico (exemplo)"})
        if ncm[:4] in ST_NCM and not str(e.get("cfop","")).startswith("5"):
            issue_list.append({"code": "CFOP_ST", "msg": "CFOP possivelmente incorreto para ST (exemplo)"})
        totals["docs"] += 1
        if issue_list: totals["suspeitas"] += 1
        findings.append({ "chave": e.get("chave"), "ncm": ncm, "cst": e.get("cst"), "cfop": e.get("cfop"), "issues": issue_list })
    return findings, totals

def run_analysis_for_upload(db: Session, upload: Upload, job: AnalysisJob) -> Report:
    raw = get_zip_bytes(upload.storage_key)
    zf = zipfile.ZipFile(io.BytesIO(raw))
    entries = []
    for name in zf.namelist():
        if name.lower().endswith(".xml"):
            xml_bytes = zf.read(name)
            try:
                entries.append(parse_xml_for_basic_fields(xml_bytes))
            except Exception:
                entries.append({"chave": name, "ncm": "", "cst": "", "cfop": "", "parse_error": True})
    findings, totals = apply_rules(entries)
    title = f"Análise Upload {upload.id} — {totals['docs']} docs, {totals['suspeitas']} com suspeita"
    rep = Report(client_id=upload.client_id, analysis_id=job.id, title=title, findings=findings, totals=totals)
    db.add(rep); db.commit(); db.refresh(rep)
    return rep
