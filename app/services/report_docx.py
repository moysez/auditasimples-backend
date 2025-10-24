# services/report_docx.py

import os
from datetime import datetime
from docx import Document

def gerar_relatorio_fiscal(totals: dict, client_name: str = "Cliente", cnpj: str = "00.000.000/0000-00"):
    doc = Document()
    data_atual = datetime.now().strftime('%d/%m/%Y')

    # 📌 Título
    doc.add_heading('Relatório Fiscal — Auditoria Monofásica (Simples Nacional)', 0)
    doc.add_paragraph(f"Empresa: {client_name}")
    doc.add_paragraph(f"CNPJ: {cnpj}")
    doc.add_paragraph(f"Período auditado: {totals.get('period_start', '---')} a {totals.get('period_end', '---')}")
    doc.add_paragraph(f"Data da análise: {data_atual}")

    # 📊 Resumo Tributário
    doc.add_heading('2. Resumo Tributário', level=1)
    trib = totals.get('tax_summary', {})
    faturamento = trib.get('faturamento', 0)
    receita_excluida = trib.get('receita_excluida', 0)
    base_corrigida = trib.get('base_corrigida', 0)
    imposto_pago = trib.get('imposto_pago', 0)
    imposto_corrigido = trib.get('imposto_corrigido', 0)
    economia = trib.get('economia_estimada', 0)
    aliquota = trib.get('aliquota_utilizada', 0) * 100

    table = doc.add_table(rows=1, cols=2)
    hdr = table.rows[0].cells
    hdr[0].text = "Descrição"
    hdr[1].text = "Valor (R$)"

    def add_row(desc, val):
        row = table.add_row().cells
        row[0].text = desc
        row[1].text = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    add_row("Faturamento Bruto", faturamento)
    add_row("Receita Monofásica Excluída", receita_excluida)
    add_row("Base Corrigida", base_corrigida)
    add_row("Alíquota utilizada (%)", aliquota)
    add_row("Imposto Pago (informado)", imposto_pago)
    add_row("Imposto Corrigido (simulado)", imposto_corrigido)
    add_row("Economia Potencial", economia)

    # 🧠 Categorias Monofásicas Identificadas
    doc.add_heading('3. Produtos Monofásicos Identificados', level=1)
    categorias = totals.get("categorias_detectadas", [])
    if categorias:
        cat_table = doc.add_table(rows=1, cols=4)
        hdr2 = cat_table.rows[0].cells
        hdr2[0].text = "Categoria"
        hdr2[1].text = "Ocorrências"
        hdr2[2].text = "Receita Total (R$)"
        hdr2[3].text = "Exemplos"
        for cat in categorias:
            exemplos = ", ".join([e["descricao"] for e in cat["exemplos"][:3]])
            total_val = sum([e["valor"] for e in cat["exemplos"]])
            row = cat_table.add_row().cells
            row[0].text = cat["categoria"].capitalize()
            row[1].text = str(cat["ocorrencias"])
            row[2].text = f"{total_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            row[3].text = exemplos
    else:
        doc.add_paragraph("Nenhuma categoria monofásica identificada.")

    # ⚖️ Fundamentação Legal
    doc.add_heading('4. Fundamentação Legal', level=1)
    doc.add_paragraph("• Lei nº 10.147/2000 — estabelece o regime monofásico de PIS/COFINS.")
    doc.add_paragraph("• Lei Complementar nº 123/2006 — art. 18 § 4º-A.")
    doc.add_paragraph("• Resolução CGSN nº 140/2018 — art. 25, § 4º.")
    doc.add_paragraph("• Conclusão: A receita decorrente da revenda de produtos sujeitos à tributação monofásica deve ser excluída da base de cálculo do DAS.")

    # 📈 Estimativa de Restituição
    economia_anual = economia * 12
    doc.add_heading('5. Estimativa de Restituição', level=1)
    doc.add_paragraph(f"💰 R$ {economia:,.2f} por mês (estimado)".replace(",", "X").replace(".", ",").replace("X", "."))
    doc.add_paragraph(f"📅 Em um ano: R$ {economia_anual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # 🪜 Próximos Passos
    doc.add_heading('6. Próximos Passos (Sugestão)', level=1)
    doc.add_paragraph("1. Conferência dos dados fiscais no PGDAS-D.")
    doc.add_paragraph("2. Correção retroativa de períodos (se aplicável).")
    doc.add_paragraph("3. Preparação de pedido de restituição/compensação.")
    doc.add_paragraph("4. Acompanhamento do processo até o reembolso.")

    # ✍️ Assinatura Digital
    doc.add_heading('7. Assinatura Digital', level=1)
    doc.add_paragraph("[NOME DO RESPONSÁVEL]")
    doc.add_paragraph("CRC / OAB / CNPJ")
    doc.add_paragraph(f"Data: {data_atual}")

    # 📂 Salvar
    filename = f"Relatorio_Fiscal_Auditoria_Monofasica_{client_name.replace(' ', '_')}.docx"
    path = os.path.join("/tmp", filename)
    doc.save(path)
    return path
