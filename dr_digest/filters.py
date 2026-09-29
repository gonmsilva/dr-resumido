"""Decide which items are worth showing to the summarizer.

Série I is legislation and is always kept. Série II is dominated by
procurement notices and public-sector HR paperwork; those are dropped here so
the summarizer only reads items that could plausibly matter to a resident,
an investor, or the housing market.
"""

from __future__ import annotations

import re

from .feeds import Item

# Série II act types that are never highlights.
DROP_TYPES = {
    "Anúncio de procedimento",  # individual public tenders
    "Louvor",
    "Declaração de Retificação",
}

# Routine HR / administrative summaries in Série II.
NOISE_PATTERNS = [
    r"procedimento concursal",
    r"concurso (documental|interno|externo)",
    r"lista (unitária )?(de )?ordenação",
    r"recrutamento",
    r"posto(s)? de trabalho",
    r"contrato de trabalho em funções públicas",
    r"mobilidade",
    r"período experimental",
    r"(sub)?delegação (e subdelegação )?de (competências|poderes)",
    r"posi(ção|cionamento) remuneratóri[oa]",
    r"aposentação|jubilação|aposentados",
    r"designação|nomeação|\bdesigna\b|\bnomeia\b",
    r"exoneração|\bexonera\b|cessação de funções|cessação da comissão",
    r"cess(ação|aram) (d[ae] )?(a )?relação jurídica de emprego",
    r"extinção do vínculo",
    r"\bpermuta entre\b",
    r"celebração de (adenda ao )?contratos? (de trabalho)?",
    r"licença sem (remuneração|vencimento)",
    r"lista provisória dos candidatos",
    r"listas? unitárias?",
    r"encarregado de proteção de dados",
    r"\bprova (psicológica|de conhecimentos)",
    r"\bjúri\b",
    r"inscrição d[oa] (dr|dra)\.?",
    r"regulamento interno do agrupamento",
    r"consolidação (definitiva )?da mobilidade",
    r"licença sem remuneração",
    r"avaliação do desempenho",
    r"funções de trabalhadores",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)


def is_candidate(item: Item) -> bool:
    if item.series == "I":
        return True
    if item.type in DROP_TYPES:
        return False
    return not NOISE_RE.search(item.summary)


def select(items: list[Item]) -> list[Item]:
    return [i for i in items if is_candidate(i)]
