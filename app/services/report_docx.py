# services/report_docx.py

import os
from datetime import datetime
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.oxml.shared import OxmlElement

def _format_table(table):
    """
    Adiciona bordas e estilo visual às tabelas.
    """
    for row in table.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ('top', 'left', 'bottom', 'right'):
                border_el = OxmlElement(f'w:{border_name}')
                border_el.set('w:val', 'single')
                border_el.set('w:sz', '8')
                border_el.set('w:space', '0')
                border_el.set('w:color', '000000')
                tcBorders.append(border_el)
            tcPr.append(tcBorders)

def gerar_relatorio_fiscal(totals: dict, client_name: str = "Cliente", cnpj: str = "00.000.000/0000-00"):
    doc = Document()
    data_atual = datetime.now().strftime('%d/%m/%Y')

    # ==============================
    # 📌 CAPA / TÍTULO
    # ==============================
    title = doc.add_heading('Relatório Fiscal — Auditoria Monofásica (Simples Nacional)', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subt = doc.add_paragraph(f"{client_name} | CNPJ: {cnpj}")
    subt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subt.runs[0].bold = True

    doc.add_paragraph(f"Período: {totals.get('period_start', '---')} a {totals.get('period_end', '---')}", style='Normal').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Data da análise: {data_atual}", style='Normal').alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("\n")

    # ==============================
    # 📊 RESUMO TRIBUTÁRIO
    # ==============================
    doc.add_heading('2. RESUMO TRIBUTÁRIO', level=1)
    trib = totals.get('tax_summary', {})
    faturamento = trib.get('faturamento', 0)
    receita_excluida = trib.get('receita_excluida', 0)
    base_corrigida = trib.get('base_corrigida', 0)
    imposto_pago = trib.get('imposto_pago', 0)
    imposto_corrigido = trib.get('imposto_corrigido', 0)
    economia = trib.get('economia_estimada', 0)
    aliquota = trib.get('aliquota_utilizada', 0) * 100

    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = "Descrição"
    hdr[1].text = "Valor (R$)"
    hdr[0].paragraphs[0].runs[0].bold = True
    hdr[1].paragraphs[0].runs[0].bold = True

    def add_row(desc, val):
        row = table.add_row().cells
        row[0].text = desc
        p = row[1].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run(f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    add_row("Faturamento Bruto", faturamento)
    add_row("Receita Monofásica Excluída", receita_excluida)
    add_row("Base Corrigida", base_corrigida)
    add_row("Alíquota utilizada (%)", aliquota)
    add_row("Imposto Pago (informado)", imposto_pago)
    add_row("Imposto Corrigido (simulado)", imposto_corrigido)
    add_row("Economia Potencial", economia)

    _format_table(table)
    doc.add_paragraph("\n")

    # ==============================
    # 🧠 CATEGORIAS MONOFÁSICAS
    # ==============================
    doc.add_heading('3. PRODUTOS MONOFÁSICOS IDENTIFICADOS', level=1)
    categorias = totals.get("categorias_detectadas", [])
    if categorias:
        cat_table = doc.add_table(rows=1, cols=4)
        hdr2 = cat_table.rows[0].cells
        hdr2[0].text = "Categoria"
        hdr2[1].text = "Ocorrências"
        hdr2[2].text = "Receita Total (R$)"
        hdr2[3].text = "Exemplos"
        for h in hdr2:
            h.paragraphs[0].runs[0].bold = True
        for cat in categorias:
            exemplos = ", ".join([e["descricao"] for e in cat["exemplos"][:3]])
            total_val = sum([e["valor"] for e in cat["exemplos"]])
            row = cat_table.add_row().cells
            row[0].text = cat["categoria"].capitalize()
            row[1].text = str(cat["ocorrencias"])
            row[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            row[2].text = f"{total_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            row[3].text = exemplos
        _format_table(cat_table)
    else:
        doc.add_paragraph("Nenhuma categoria monofásica identificada.")

    doc.add_paragraph("\n")

    # ==============================
    # ⚖️ FUNDAMENTAÇÃO LEGAL
    # ==============================
    doc.add_heading('4. FUNDAMENTAÇÃO LEGAL', level=1)
    doc.add_paragraph("• Lei nº 10.147/2000 — estabelece o regime monofásico de PIS/COFINS.")
    doc.add_paragraph("• Lei Complementar nº 123/2006 — art. 18 § 4º-A.")
    doc.add_paragraph("• Resolução CGSN nº 140/2018 — art. 25, § 4º.")
    doc.add_paragraph("• Conclusão: A receita decorrente da revenda de produtos sujeitos à tributação monofásica deve ser excluída da base de cálculo do DAS.")
    doc.add_paragraph("\n")

    # ==============================
    # 📈 ESTIMATIVA
    # ==============================
    doc.add_heading('5. ESTIMATIVA DE RESTITUIÇÃO', level=1)
    economia_anual = economia * 12
    p1 = doc.add_paragraph(f"💰 R$ {economia:,.2f} por mês (estimado)".replace(",", "X").replace(".", ",").replace("X", "."))
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2 = doc.add_paragraph(f"📅 Em um ano: R$ {economia_anual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n")

    # ==============================
    # 🪜 PRÓXIMOS PASSOS
    # ==============================
    doc.add_heading('6. PRÓXIMOS PASSOS (SUGESTÃO)', level=1)
    passos = [
        "1. Conferência dos dados fiscais no PGDAS-D.",
        "2. Correção retroativa de períodos (se aplicável).",
        "3. Preparação de pedido de restituição/compensação.",
        "4. Acompanhamento do processo até o reembolso."
    ]
    for p in passos:
        doc.add_paragraph(p)
    doc.add_paragraph("\n")

    # ==============================
    # ✍️ ASSINATURA
    # ==============================
    doc.add_heading('7. ASSINATURA DIGITAL', level=1)
    doc.add_paragraph("[NOME DO RESPONSÁVEL]")
    doc.add_paragraph("CRC / OAB / CNPJ")
    doc.add_paragraph(f"Data: {data_atual}")

    # 📂 Salvar
    filename = f"Relatorio_Fiscal_Auditoria_Monofasica_{client_name.replace(' ', '_')}.docx"
    path = os.path.join("/tmp", filename)
    doc.save(path)
    return path
