"""Tradução do vocabulário do CSV pro vocabulário do app — meio de
pagamento, tipo de movimento e estrutura de custo. Ver docs/backlog.md
("Migração de dados do app antigo") pro porquê de cada mapeamento."""
from __future__ import annotations

from collections import defaultdict

from .parsing import Lancamento

CUSTO_MAP: dict[str, str] = {
    "Custos Fixos": "fixo",
    "Custos Variáveis": "variavel",
    "Sazonalidades": "sazonal",
}

# (Movimentação, Tipo do Pag / Movimento) do CSV -> tipo_movimento do app
TIPO_MOVIMENTO_MAP: dict[tuple[str, str], str] = {
    ("Despesa", "Compra à vista"): "despesa",
    ("Despesa", "Parcela sem juros"): "despesa",
    ("Despesa", "Compra internacional"): "despesa",
    ("Despesa", "Estorno"): "estorno",
    ("Despesa", "Ressarcimento"): "ressarcimento",
    ("Receita", "Recebimento"): "receita",
    ("Reserva", "Aplicação"): "aplicacao",
    ("Reserva", "Retirada"): "retirada",
}

# só ocorre em Receita, que não exige meio_pagamento (decidido com o
# usuário) — por isso mapeia pra None em vez de inventar um valor novo
# no enum do app
MEIO_PAGAMENTO_MAP: dict[str, str | None] = {
    "Pix": "pix",
    "Cartão de Débito": "cartao_debito",
    "Cartão de Crédito": "cartao_credito",
    "Boleto": "boleto",
    "Débito Automático": "debito_automatico",
    "Crédito em Conta": None,
    "": None,
}


def resolver_tipo_movimento(movimentacao: str, tipo_pag_movimento: str) -> str:
    try:
        return TIPO_MOVIMENTO_MAP[(movimentacao, tipo_pag_movimento)]
    except KeyError:
        raise ValueError(
            f"Combinação Movimentação/Tipo não mapeada: {movimentacao!r} / {tipo_pag_movimento!r}"
        ) from None


def resolver_meio_pagamento(bruto: str) -> str | None:
    try:
        return MEIO_PAGAMENTO_MAP[bruto]
    except KeyError:
        raise ValueError(f"Meio de pagamento não mapeado: {bruto!r}") from None


def resolver_valor(valor_csv: float) -> float:
    """Estorno usa sinal negativo no CSV como convenção própria do
    usuário (diferenciar de ressarcimento) — o schema novo guarda sempre
    valor positivo, o sinal fica implícito no `tipo_movimento`."""
    return round(abs(valor_csv), 2)


def aprender_estrutura_custo_por_subcategoria(lancamentos: list[Lancamento]) -> dict[tuple[str, str], str]:
    """Pra cada (categoria, subcategoria), se todas as linhas já
    preenchidas concordam num único valor de `Custo`, aprende esse valor
    como default pros vazios da mesma subcategoria. Subcategorias sem
    nenhum dado ou com valores divergentes entre linhas ficam de fora —
    são exatamente as que precisam de decisão manual (overrides.py)."""
    vistos: dict[tuple[str, str], set[str]] = defaultdict(set)
    for l in lancamentos:
        if l.movimentacao != "Despesa" or not l.custo:
            continue
        vistos[(l.categoria, l.subcategoria)].add(l.custo)

    return {chave: CUSTO_MAP[valores.pop()] for chave, valores in vistos.items() if len(valores) == 1}


def resolver_estrutura_custo(
    lancamento: Lancamento,
    aprendido: dict[tuple[str, str], str],
    overrides: dict[str, str | None],
    chave_override: str,
) -> str | None:
    """Ordem de resolução: (1) valor literal do CSV, (2) valor aprendido
    da subcategoria, (3) resposta interativa salva em overrides. `None`
    = ainda pendente."""
    if lancamento.custo:
        return CUSTO_MAP[lancamento.custo]
    chave_sub = (lancamento.categoria, lancamento.subcategoria)
    if chave_sub in aprendido:
        return aprendido[chave_sub]
    return overrides.get(chave_override)
