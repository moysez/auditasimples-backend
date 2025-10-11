from __future__ import annotations
from typing import Dict, Any
import io
import zipfile
import logging
from datetime import datetime
from .nfe import parse_nfe_xml
from .ai_matcher import matcher

# 🧭 Configuração de logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 🧾 Função auxiliar para validar NCM
def _has_valid_ncm(ncm: str) -> bool:
    n = (ncm or '').strip()
    return len(n) == 8 and n.isdigit()

# 📊 Inicialização das métricas
def init_totals() -> dict:
    return {
        # 📄 Documentos e valores
        'documents': 0,
        'total_value_sum': 0.0,
        'period_start': None,
        'period_end': None,
        'items': 0,

        # 📊 Indicadores monofásicos
        'monofasico_sem_ncm': 0,
        'monofasico_palavra_chave': 0,
        'monofasico_ia_detectado': 0,

        # 🧾 Regras fiscais
        'st_cfop_csosn_corretos': 0,
        'st_incorreta': 0,

        # 🚨 Erros e inconsistências
        'erros_ncm_categoria': 0,
        'erros_outros': 0,
    }

# 🧠 Função principal de análise
def run_analysis_from_bytes(zip_bytes: bytes) -> Dict[str, Any]:
    totals = init_totals()

    logger.info("🚀 Iniciando análise fiscal...")
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        xml_files = [name for name in zf.namelist() if name.lower().endswith('.xml')]
        logger.info(f"📦 {len(xml_files)} arquivos XML encontrados no ZIP")

        for idx, name in enumerate(xml_files, 1):
            logger.info(f"📄 Processando arquivo {idx}/{len(xml_files)}: {name}")
            try:
                xml_bytes = zf.read(name)
                doc = parse_nfe_xml(xml_bytes)
            except Exception as e:
                logger.error(f"❌ Erro ao processar arquivo {name}: {e}")
                totals['erros_outros'] += 1
                continue

            totals['documents'] += 1
            totals['total_value_sum'] += doc.get('total_value', 0.0)

            dt = doc.get('issue_date')
            if dt:
                if totals['period_start'] is None or dt < totals['period_start']:
                    totals['period_start'] = dt
                if totals['period_end'] is None or dt > totals['period_end']:
                    totals['period_end'] = dt

            for item_idx, item in enumerate(doc.get('items', []), 1):
                desc = item.get('xProd', '')
                ncm  = item.get('ncm', '')
                cfop = item.get('cfop', '')
                csosn = item.get('csosn', '')

                logger.debug(f"🧾 Item {item_idx}: {desc} | NCM={ncm} | CFOP={cfop} | CSOSN={csosn}")
                totals['items'] += 1

                # 1) Fuzzy Match da descrição
                hit = matcher.classify(desc)
                if hit:
                    cat, _score = hit
                    logger.info(f"   🟢 Categoria detectada: {cat} (score: {_score:.2f})")

                    if matcher.is_monofasico(cat):
                        totals['monofasico_palavra_chave'] += 1
                        logger.warning(f"   ⚠️ Produto monofásico detectado: {desc}")
                        if not _has_valid_ncm(ncm):
                            totals['monofasico_sem_ncm'] += 1
                            logger.warning(f"   ❌ NCM inválido ou ausente: {ncm}")

                    # 2) Valida NCM com categoria detectada
                    val = matcher.validate_ncm_for_category(ncm, cat)
                    if not val["ncm_valido"]:
                        totals['erros_ncm_categoria'] += 1
                        logger.error(f"   🚨 NCM incompatível com categoria ({ncm} x {cat})")
                else:
                    logger.debug("   ⚪ Nenhuma categoria fuzzy detectada")

                # 3) Valida CFOP/CSOSN
                if cfop == '5405' and csosn == '500':
                    totals['st_cfop_csosn_corretos'] += 1
                else:
                    totals['st_incorreta'] += 1
                    logger.error(f"   ❌ CFOP/CSOSN incorretos: {cfop}/{csosn}")

    # 🕒 Ajusta datas
    if totals['period_start']:
        totals['period_start'] = totals['period_start'].isoformat()
    if totals['period_end']:
        totals['period_end'] = totals['period_end'].isoformat()

    # 💰 Cálculo de economia simulada
    totals['savings_simulated'] = round(0.005 * totals['total_value_sum'], 2)

    # 📊 Resumo final
    logger.info("✅ Análise finalizada com sucesso!")
    logger.info(f"📊 Documentos: {totals['documents']}")
    logger.info(f"📦 Itens: {totals['items']}")
    logger.info(f"💰 Valor total: R$ {totals['total_value_sum']:.2f}")
    logger.info(f"⚠️ Monofásicos (descrição): {totals['monofasico_palavra_chave']}")
    logger.info(f"🚨 Erros NCM x Categoria: {totals['erros_ncm_categoria']}")
    logger.info(f"📌 CFOP/CSOSN corretos: {totals['st_cfop_csosn_corretos']}")
    logger.info(f"💰 Economia simulada: R$ {totals['savings_simulated']:.2f}")

    return totals
