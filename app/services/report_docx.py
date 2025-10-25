# services/report_docx.py
import os
from datetime import datetime
from typing import Any, Dict
from collections import defaultdict

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement

# ==========================
# Utilitários internos
# ==========================
def _fmt_money(v: Any) -> str:
    try:
        n = float(v or 0.0)
    except Exception:
        n = 0.0
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_percent(v: Any) -> str:
    try:
        n = float(v or 0.0) * 100
    except Exception:
        n = 0.0
    return f"{n:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


    def _format_table_borders(table):
        for row in table.rows:
            for cell in row.cells:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcBorders = OxmlElement("w:tcBorders")
                for b in ("top", "left", "bottom", "right"):
                    el = OxmlElement(f"w:{b}")
                    # AQUI: removido prefixo do atributo 'w:val'
                    el.set("val", "single")
                    el.set("sz", "8")
                    el.set("space", "0")
                    el.set("color", "000000")
                    tcBorders.append(el)
                tcPr.append(tcBorders)
    
    def _add_row(tbl, label, value):
    r = tbl.add_row().cells
    r[0].text = str(label)
    r[1].text = str(value)


# ==========================
# Geração do Relatório DOCX
# ==========================
def gerar_relatorio_fiscal(
    totals: Dict[str, Any],
    client_name: str = "Cliente",
    cnpj: str = "00.000.000/0000-00",
) -> str:
    totals = totals or {}
    tax = totals.get("tax_summary") or {}

    period_start = totals.get("period_start") or "---"
    period_end = totals.get("period_end") or "---"

    documentos = totals.get("documents", 0) or 0
    itens = totals.get("items", 0) or 0
    valor_total = totals.get("total_value_sum", 0.0) or 0.0

    faturamento = tax.get("faturamento", valor_total) or 0.0
    receita_excluida = tax.get("receita_excluida", 0.0) or 0.0
    base_corrigida = tax.get("base_corrigida", 0.0) or (faturamento - receita_excluida)
    imposto_pago = tax.get("imposto_pago", 0.0) or 0.0
    imposto_corrigido = tax.get("imposto_corrigido", 0.0) or 0.0
    economia = tax.get("economia_estimada", 0.0) or 0.0
    aliquota_frac = tax.get("aliquota_utilizada", 0.0) or 0.0

    erros = totals.get("erros_fiscais") or {}
    st_corretos = erros.get("st_corretos", totals.get("st_cfop_csosn_corretos", 0) or 0)
    st_incorretos = erros.get("st_incorretos", totals.get("st_incorreta", 0) or 0)
    mono_sem_ncm = erros.get("monofasico_ncm_incorreto", totals.get("monofasico_sem_ncm", 0) or 0)
    mono_desc = erros.get("monofasico_desc", totals.get("monofasico_palavra_chave", 0) or 0)

    categorias_detectadas = erros.get("categorias_detectadas") or totals.get("categorias_detectadas") or []
    produtos_duplicados = erros.get("produtos_duplicados") or totals.get("produtos_duplicados") or []

    doc = Document()
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # ==========================
    # CAPA
    # ==========================
    h = doc.add_heading("Relatório Fiscal — Auditoria Monofásica (Simples Nacional)", 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(f"{client_name}  |  CNPJ: {cnpj}")
    p.runs[0].bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2 = doc.add_paragraph(f"Período auditado: {period_start} — {period_end}")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3 = doc.add_paragraph(f"Data da análise: {data_hoje}")
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    # ==========================
    # 1. Resumo Geral
    # ==========================
    doc.add_heading("1. Resumo Geral", level=1)
    t_resumo = doc.add_table(rows=1, cols=2)
    t_resumo.style = "Table Grid"
    t_resumo.cell(0, 0).text = "Indicador"
    t_resumo.cell(0, 1).text = "Valor"
    t_resumo.rows[0].cells[0].paragraphs[0].runs[0].bold = True
    t_resumo.rows[0].cells[1].paragraphs[0].runs[0].bold = True
    _add_row(t_resumo, "Documentos analisados", documentos)
    _add_row(t_resumo, "Itens analisados", itens)
    _add_row(t_resumo, "Faturamento bruto (soma NF-e)", f"R$ {_fmt_money(faturamento)}")
    _format_table_borders(t_resumo)
    doc.add_paragraph("")

    # ==========================
    # 2. Resumo Tributário
    # ==========================
    doc.add_heading("2. Resumo Tributário", level=1)
    t_trib = doc.add_table(rows=1, cols=2)
    t_trib.style = "Table Grid"
    t_trib.cell(0, 0).text = "Descrição"
    t_trib.cell(0, 1).text = "Valor"
    t_trib.rows[0].cells[0].paragraphs[0].runs[0].bold = True
    t_trib.rows[0].cells[1].paragraphs[0].runs[0].bold = True
    _add_row(t_trib, "Faturamento Bruto", f"R$ {_fmt_money(faturamento)}")
    _add_row(t_trib, "Receita Monofásica Excluída", f"R$ {_fmt_money(receita_excluida)}")
    _add_row(t_trib, "Base Corrigida", f"R$ {_fmt_money(base_corrigida)}")
    _add_row(t_trib, "Alíquota utilizada", _fmt_percent(aliquota_frac))
    _add_row(t_trib, "Imposto Pago", f"R$ {_fmt_money(imposto_pago)}")
    _add_row(t_trib, "Imposto Corrigido", f"R$ {_fmt_money(imposto_corrigido)}")
    _add_row(t_trib, "Economia Estimada", f"R$ {_fmt_money(economia)}")
    _format_table_borders(t_trib)
    doc.add_paragraph("")

    # ==========================
    # 3. Erros Fiscais
    # ==========================
    doc.add_heading("3. Erros Fiscais", level=1)
    t_err = doc.add_table(rows=1, cols=2)
    t_err.style = "Table Grid"
    t_err.cell(0, 0).text = "Indicador"
    t_err.cell(0, 1).text = "Quantidade"
    t_err.rows[0].cells[0].paragraphs[0].runs[0].bold = True
    t_err.rows[0].cells[1].paragraphs[0].runs[0].bold = True
    _add_row(t_err, "Monofásicos (IA)", mono_desc)
    _add_row(t_err, "Monofásicos sem NCM", mono_sem_ncm)
    _add_row(t_err, "ST corretos", st_corretos)
    _add_row(t_err, "ST incorretos", st_incorretos)
    _format_table_borders(t_err)
    doc.add_paragraph("")

    # ==========================
    # 4. Detalhamento Analítico dos Itens Excluídos
    # ==========================
    produtos = totals.get("products") or []
    produtos_excluidos = [p for p in produtos if p.get("monofasico", True)]
    if produtos_excluidos:
        doc.add_heading("4. Detalhamento Analítico dos Itens Excluídos", level=1)
        grupos = defaultdict(list)
        for item in produtos_excluidos:
            data = item.get("data_emissao")
            try:
                mes_ref = datetime.fromisoformat(data).strftime("%Y-%m") if data else "Sem Data"
            except Exception:
                mes_ref = "Sem Data"
            grupos[mes_ref].append(item)

        total_geral = 0.0
        for mes, lista in sorted(grupos.items()):
            doc.add_heading(f"Mês de referência: {mes}", level=2)
            tabela = doc.add_table(rows=1, cols=10)
            tabela.style = "Table Grid"
            headers = [
                "Data", "Documento", "Código", "Descrição", "NCM",
                "NCM/CEST Recomendado", "Qtd", "Vlr Unit", "Vlr Total", "Chave"
            ]
            for idx, htxt in enumerate(headers):
                tabela.cell(0, idx).text = htxt
                tabela.cell(0, idx).paragraphs[0].runs[0].bold = True

            subtotal_mes = 0.0
            for it in lista:
                r = tabela.add_row().cells
                r[0].text = str(it.get("data_emissao") or "-")
                r[1].text = str(it.get("numero") or "-")
                r[2].text = str(it.get("codigo") or "-")
                r[3].text = str(it.get("descricao") or "-")
                r[4].text = str(it.get("ncm") or "-")
                recomend = f"{it.get('ncm_recomendado') or '-'} / {it.get('cest') or '-'}"
                r[5].text = recomend
                r[6].text = str(it.get("quantidade") or "-")
                r[7].text = f"R$ {_fmt_money(it.get('valor_unitario') or 0)}"
                r[8].text = f"R$ {_fmt_money(it.get('valor_total') or 0)}"
                r[9].text = str(it.get("chave") or "-")
                subtotal_mes += float(it.get("valor_total") or 0.0)

            _format_table_borders(tabela)
            doc.add_paragraph(f"Subtotal mês {mes}: R$ {_fmt_money(subtotal_mes)}")
            total_geral += subtotal_mes

        doc.add_paragraph(f"TOTAL GERAL DOS ITENS EXCLUÍDOS: R$ {_fmt_money(total_geral)}")
        doc.add_paragraph("")

    # ==========================
    # 5. Fundamentação Legal
    # ==========================
    doc.add_heading("5. Fundamentação Legal", level=1)
    doc.add_paragraph("• Lei nº 10.147/2000 — regime monofásico de PIS/COFINS.")
    doc.add_paragraph("• Lei Complementar nº 123/2006 — art. 18 § 4º-A.")
    doc.add_paragraph("• Resolução CGSN nº 140/2018 — art. 25, § 4º.")
    doc.add_paragraph("Conclusão: receita monofásica deve ser excluída da base de cálculo do DAS.")

    # ==========================
    # 6. Estimativa de Restituição
    # ==========================
    doc.add_heading("6. Estimativa de Restituição", level=1)
    economia_anual = float(economia) * 12
    p_est1 = doc.add_paragraph(f"💰 R$ {_fmt_money(economia)} por mês (estimado)")
    p_est1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_est2 = doc.add_paragraph(f"📅 Em um ano: R$ {_fmt_money(economia_anual)}")
    p_est2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ==========================
    # 7. Próximos Passos
    # ==========================
    doc.add_heading("7. Próximos Passos", level=1)
    passos = [
        "1. Conferir dados no PGDAS-D.",
        "2. Retificar períodos passados (se aplicável).",
        "3. Preparar pedido de restituição/compensação.",
        "4. Acompanhar até o reembolso.",
    ]
    for s in passos:
        doc.add_paragraph(s)

    # ==========================
    # 8. Assinatura Digital
    # ==========================
    doc.add_heading("8. Assinatura Digital", level=1)
    doc.add_paragraph("[NOME DO RESPONSÁVEL]")
    doc.add_paragraph("CRC / OAB / CNPJ")
    doc.add_paragraph(f"Data: {data_hoje}")

    filename = f"Relatorio_Fiscal_Auditoria_Monofasica_{client_name.replace(' ', '_')}.docx"
    path = os.path.join("/tmp", filename)
    doc.save(path)
    return path
