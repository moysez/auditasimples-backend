import logging
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

# Pasta onde os relatórios serão salvos
REPORTS_DIR = Path("/tmp/relatorios_fiscais")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Funções auxiliares
# -------------------------
def safe_float(value):
    """Converte valor para float, retornando 0.0 em caso de None ou inválido."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_paragraph(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(str(text))
    if bold:
        run.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_key_value(doc, key, value):
    p = doc.add_paragraph()
    p.add_run(f"{key}: ").bold = True
    p.add_run(str(value))


# -------------------------
# Função principal
# -------------------------
def gerar_relatorio_fiscal(totals: dict, client_name: str) -> str:
    """
    Gera o relatório fiscal DOCX com base nos dados agregados de análise tributária.
    """

    trib = totals.get('tax_summary') or {}

    # Sanitiza valores numéricos
    faturamento = safe_float(trib.get('faturamento'))
    receita_excluida = safe_float(trib.get('receita_excluida'))
    base_corrigida = safe_float(trib.get('base_corrigida'))
    imposto_pago = safe_float(trib.get('imposto_pago'))
    imposto_corrigido = safe_float(trib.get('imposto_corrigido'))
    economia = safe_float(trib.get('economia_estimada'))
    aliquota = safe_float(trib.get('aliquota_utilizada')) * 100

    # Log de depuração
    logger.info(f"[DEBUG DOCX] faturamento={faturamento}, receita_excluida={receita_excluida}, "
                f"base_corrigida={base_corrigida}, imposto_corrigido={imposto_corrigido}, aliquota={aliquota}")

    # Evita divisão por zero
    economia_percent = (economia / faturamento * 100) if faturamento else 0.0

    # -------------------------
    # Montagem do DOCX
    # -------------------------
    doc = Document()

    # Título
    title = doc.add_heading(f"Relatório Fiscal - {client_name}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    doc.add_heading("📊 Resumo Tributário", level=1)
    add_key_value(doc, "Faturamento", f"R$ {faturamento:,.2f}")
    add_key_value(doc, "Base Corrigida", f"R$ {base_corrigida:,.2f}")
    add_key_value(doc, "Receita Excluída", f"R$ {receita_excluida:,.2f}")
    add_key_value(doc, "Imposto Pago", f"R$ {imposto_pago:,.2f}")
    add_key_value(doc, "Imposto Corrigido", f"R$ {imposto_corrigido:,.2f}")
    add_key_value(doc, "Economia Estimada", f"R$ {economia:,.2f}")
    add_key_value(doc, "Percentual de Economia", f"{economia_percent:.2f}%")
    add_key_value(doc, "Alíquota Utilizada", f"{aliquota:.2f}%")

    # -------------------------
    # Itens e categorias detectadas
    # -------------------------
    produtos = totals.get("products", [])
    categorias = totals.get("categorias_detectadas", [])

    doc.add_heading("📦 Produtos Analisados", level=1)
    add_paragraph(doc, f"Total de itens analisados: {len(produtos)}")

    # Top 10 produtos mais relevantes
    produtos_top = sorted(produtos, key=lambda x: float(x.get("valor_total", 0)), reverse=True)[:10]
    for p in produtos_top:
        desc = p.get("descricao") or p.get("xProd") or "N/A"
        valor = safe_float(p.get("valor_total"))
        add_paragraph(doc, f"{desc} — R$ {valor:,.2f}")

    # Categorias
    if categorias:
        doc.add_heading("🏷 Categorias Detectadas (IA)", level=1)
        for cat in categorias:
            add_paragraph(doc, f"{cat.get('categoria')} — {cat.get('ocorrencias')} ocorrências")
            exemplos = cat.get("exemplos", [])
            for ex in exemplos:
                add_paragraph(doc, f" • {ex.get('descricao')} (score {ex.get('score')})")

    # -------------------------
    # Rodapé
    # -------------------------
    doc.add_heading("📌 Observações", level=1)
    add_paragraph(
        doc,
        "Este relatório foi gerado automaticamente com base nos documentos fiscais eletrônicos do cliente. "
        "Os valores de economia estimada representam uma simulação com base na legislação vigente."
    )

    # -------------------------
    # Salvamento
    # -------------------------
    safe_name = client_name.replace(" ", "_").replace("/", "_")
    output_path = REPORTS_DIR / f"Relatorio_Fiscal_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    doc.save(str(output_path))

    logger.info(f"📄 Relatório fiscal gerado com sucesso: {output_path}")

    return str(output_path)
