"""Agrupamento de compras parceladas — reconstrói o vínculo que o app
antigo nunca guardou (cada parcela era uma linha solta, sem
compra_parcelada_id). Ver docs/backlog.md pro achado que motivou a
checagem cronológica: sem ela, duas compras diferentes do "Flamengo
Nação" (mesma descrição, mesmo total de 12 parcelas, uma terminando e
outra começando no mesmo mês) se uniam numa só, porque os números 1-12
apareciam completos ao juntar as duas."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .parsing import Lancamento

TIPO_PARCELA_SEM_JUROS = "Parcela sem juros"

_PADRAO_PARCELA = re.compile(r"^(.*?)\s*\((\d+)/(\d+)\)(.*)$")


@dataclass
class GrupoParcela:
    descricao: str
    parcela_total: int
    categoria: str
    subcategoria: str
    banco: str
    # (parcela_atual, lançamento), já em ordem cronológica
    itens: list[tuple[int, Lancamento]]

    @property
    def valor_total(self) -> float:
        return round(sum(abs(l.valor) for _, l in self.itens), 2)

    @property
    def completo(self) -> bool:
        """True só se a sequência migrada vai de 1 até parcela_total —
        um grupo incompleto não é erro (a parte que falta ficou fora da
        janela do CSV), só não gera todas as parcelas ainda."""
        return self.itens[0][0] == 1 and self.itens[-1][0] == self.parcela_total


def extrair_parcela(descricao: str) -> tuple[str, int, int, str] | None:
    """'Globo Premiere (8/12)' -> ('Globo Premiere', 8, 12, ''). `None`
    se a descrição não seguir o padrão `(N/M)`."""
    m = _PADRAO_PARCELA.match(descricao)
    if not m:
        return None
    base, n, total, resto = m.groups()
    return base.strip(), int(n), int(total), resto.strip()


def agrupar_parcelas(lancamentos: list[Lancamento]) -> tuple[list[GrupoParcela], list[Lancamento]]:
    """Devolve (grupos, linhas_sem_padrao). `linhas_sem_padrao` são
    'Parcela sem juros' cuja Descrição não bate com `(N/M)` — mantido
    como salvaguarda pra rodadas futuras do CSV, hoje deve vir vazio."""
    candidatos: dict[tuple[str, int, str, str, str, str], list[tuple[int, Lancamento]]] = {}
    sem_padrao: list[Lancamento] = []

    for l in lancamentos:
        if l.tipo_pag_movimento != TIPO_PARCELA_SEM_JUROS:
            continue
        extraido = extrair_parcela(l.descricao)
        if extraido is None:
            sem_padrao.append(l)
            continue
        base, n, total, resto = extraido
        chave = (base, total, resto, l.categoria, l.subcategoria, l.banco)
        candidatos.setdefault(chave, []).append((n, l))

    grupos: list[GrupoParcela] = []
    for (base, total, resto, categoria, subcategoria, banco), itens in candidatos.items():
        itens.sort(key=lambda par: par[1].data)
        ciclo: list[tuple[int, Lancamento]] = []
        for n, l in itens:
            # reinício (N volta a ser menor) ou salto na sequência = uma
            # compra nova, não continuação da anterior
            if ciclo and n != ciclo[-1][0] + 1:
                grupos.append(GrupoParcela(base, total, categoria, subcategoria, banco, ciclo))
                ciclo = []
            ciclo.append((n, l))
        if ciclo:
            grupos.append(GrupoParcela(base, total, categoria, subcategoria, banco, ciclo))

    return grupos, sem_padrao
