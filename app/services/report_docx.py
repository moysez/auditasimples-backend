# services/report_docx.py

import os
from datetime import datetime
from docx import Document

def gerar_relatorio_fiscal(totals: dict, client_name: str = "Cliente"):
    """
    Gera Relatorio_Fiscal_Auditoria_Monofasica.docx com base nos dados de análise.
    """
    doc = Document()
    doc.add_heading('Relatório Fiscal - Auditoria Monofásica', 0)
    doc.add_paragraph(f"Empresa: {client_name}")
    doc.add_paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    doc.add_heading('📊 Dados Tributários', level=1)
    trib = totals.get('tax_summary', {})
    faturamento = trib.get('faturamento', 0)
    receita_excluida = trib.get('receita_excluida', 0)
    base_corrigida = trib.get('base_corrigida', 0)
    imposto_pago = trib.get('imposto_pago', 0)
    imposto_corrigido = trib.get('imposto_corrigido', 0)
    economia = trib.get('economia_estimada', 0)

    doc.add_paragraph(f"Faturamento: R$ {faturamento:,.2f}")
    doc.add_paragraph(f"Receita Excluída: R$ {receita_excluida:,.2f}")
    doc.add_paragraph(f"Base Corrigida: R$ {base_corrigida:,.2f}")
    doc.add_paragraph(f"Imposto Pago: R$ {imposto_pago:,.2f}")
    doc.add_paragraph(f"Imposto Corrigido: R$ {imposto_corrigido:,.2f}")
    doc.add_paragraph(f"Economia Estimada: R$ {economia:,.2f}")

    doc.add_heading('🚨 Erros Fiscais', level=1)
    doc.add_paragraph(f"ST Corretos: {totals.get('st_cfop_csosn_corretos', 0)}")
    doc.add_paragraph(f"ST Incorretos: {totals.get('st_incorreta', 0)}")
    doc.add_paragraph(f"Monofásicos identificados: {totals.get('monofasico_palavra_chave', 0)}")
    doc.add_paragraph(f"Monofásicos sem NCM: {totals.get('monofasico_sem_ncm', 0)}")
    doc.add_paragraph(f"Erros NCM x Categoria: {totals.get('erros_ncm_categoria', 0)}")

    doc.add_heading('📅 Período analisado', level=1)
    doc.add_paragraph(f"Início: {totals.get('period_start', '---')}")
    doc.add_paragraph(f"Fim: {totals.get('period_end', '---')}")

    filename = f"Relatorio_Fiscal_Auditoria_Monofasica_{client_name.replace(' ', '_')}.docx"
    path = os.path.join("/tmp", filename)
    doc.save(path)
    return path
