import os
from datetime import datetime
from typing import Any, Dict
from collections import defaultdict

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def _fmt_money(v: Any) -> str:
    try:
        n = float(v or 0.0)
    except Exception:
        n = 0.0
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _fmt_percent(frac: Any) -> str:
    try:
        n = float(frac or 0.0)
    except Exception:
        n = 0.0
    n = n * 100.0
    return f"{n:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def _format_table_borders(table) -> None:
    tbl = table._tbl
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        tblBorders.append(el)
    tbl.tblPr.append(tblBorders)

def _add_row(tbl, label: Any, value: Any) -> None:
    r = tbl.add_row().cells
    r[0].text = "" if label is None else str(label)
    r[1].text = "" if value is None else str(value)

def gerar_relatorio_fiscal(totals: Dict[str, Any], client_name: str = "Cliente", cnpj: str = "00.000.000/0000-00") -> str:
    totals = totals or {}
    tax = totals.get("tax_summary") or {}

    period_start = totals.get("period_start") or "---"
    period_end   = totals.get("period_end") or "---"

    documentos  = totals.get("documents", 0) or 0
    itens       = totals.get("items", 0) or 0
    valor_total = totals.get("total_value_sum", 0.0) or 0.0

    faturamento     = tax.get("faturamento", valor_total) or 0.0
    receita_excluida= tax.get("receita_excluida", 0.0) or 0.0
    base_corrigida  = tax.get("base_corrigida", faturamento - receita_excluida) or 0.0
    imposto_pago    = tax.get("imposto_pago", 0.0) or 0.0
    imposto_corrigido = tax.get("imposto_corrigido", 0.0) or 0.0
    economia        = tax.get("economia_estimada", 0.0) or 0.0
    aliquota_frac   = tax.get("aliquota_utilizada", 0.0) or 0.0

    produtos_duplicados = totals.get("produtos_duplicados") or []

    doc = Document()
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    h = doc.add_heading("Relatório de Auditoria Fiscal — (Simples Nacional)", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f"{client_name}  |  CNPJ: {cnpj}")
    p.runs[0].bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2 = doc.add_paragraph(f"Período auditado: {period_start} — {period_end}")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3 = doc.add_paragraph(f"Data da análise: {data_hoje}")
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    # 1. Resumo Geral
    doc.add_heading("1. Resumo Geral", level=1)
    t_resumo = doc.add_table(rows=1, cols=2)
    t_resumo.style = "Table Grid"
    t_resumo.cell(0,0).text="Indicador"
    t_resumo.cell(0,1).text="Valor"
    for c in t_resumo.rows[0].cells: c.paragraphs[0].runs[0].bold = True
    _add_row(t_resumo, "Documentos analisados", documentos)
    _add_row(t_resumo, "Itens analisados", itens)
    _add_row(t_resumo, "Faturamento bruto (soma NF-e)", f"R$ {_fmt_money(faturamento)}")
    _format_table_borders(t_resumo)
    doc.add_paragraph("")

    # 2. Resumo Tributário
    doc.add_heading("2. Resumo Tributário", level=1)
    t_trib = doc.add_table(rows=1, cols=2)
    t_trib.style = "Table Grid"
    t_trib.cell(0,0).text="Descrição"
    t_trib.cell(0,1).text="Valor"
    for c in t_trib.rows[0].cells: c.paragraphs[0].runs[0].bold = True
    _add_row(t_trib, "Faturamento Bruto",            f"R$ {_fmt_money(faturamento)}")
    _add_row(t_trib, "Receita Monofásica Excluída", f"R$ {_fmt_money(receita_excluida)}")
    _add_row(t_trib, "Base Corrigida",              f"R$ {_fmt_money(base_corrigida)}")
    _add_row(t_trib, "Alíquota utilizada",           _fmt_percent(aliquota_frac))
    _add_row(t_trib, "Imposto Pago",                f"R$ {_fmt_money(imposto_pago)}")
    _add_row(t_trib, "Imposto Corrigido",           f"R$ {_fmt_money(imposto_corrigido)}")
    _add_row(t_trib, "Economia Estimada",           f"R$ {_fmt_money(economia)}")
    _format_table_borders(t_trib)
    doc.add_paragraph("")

    # 4. Itens Deduplicados (por descrição)
    if produtos_duplicados:
        doc.add_heading("4. Itens Deduplicados (por descrição)", level=1)
        t_dup = doc.add_table(rows=1, cols=4)
        t_dup.style = "Table Grid"
        hdr = t_dup.rows[0].cells
        hdr[0].text = "Código"
        hdr[1].text = "Descrição"
        hdr[2].text = "Ocorrências"
        hdr[3].text = "Valor Total"
        for c in hdr:
            c.paragraphs[0].runs[0].bold = True

        for item in produtos_duplicados:
            r = t_dup.add_row().cells
