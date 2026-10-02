"""Mapeamento fixo de contas — decidido com o usuário (ver docs/backlog.md):
BTG vira 2 contas (corrente + cartão, hoje misturadas na coluna `Banco`
do CSV), as demais são 1:1."""
from __future__ import annotations

BTG_CORRENTE = "BTG Corrente"
BTG_CARTAO = "BTG Cartão"

# nome -> payload de criação (bate com ContaCreate em app/schemas/contas.py)
CONTAS: dict[str, dict] = {
    BTG_CORRENTE: {"tipo_conta": "corrente", "banco": "BTG"},
    BTG_CARTAO: {"tipo_conta": "cartao_credito", "banco": "BTG", "dia_fechamento": 8, "dia_vencimento": 11},
    "Mercado Pago Wagner": {"tipo_conta": "corrente", "banco": "Mercado Pago"},
    "Mercado Pago Josi": {"tipo_conta": "corrente", "banco": "Mercado Pago Josi"},
    "Banco do Brasil": {"tipo_conta": "corrente", "banco": "Banco do Brasil"},
    "Pluxee": {"tipo_conta": "carteira", "banco": "Pluxee"},
}

# nome do banco como aparece na coluna `Banco` do CSV -> nome da conta,
# pros bancos que não precisam de split (BTG é tratado à parte)
_BANCO_CSV_PARA_CONTA = {
    "Mercado Pago": "Mercado Pago Wagner",
    "Mercado Pago Josi": "Mercado Pago Josi",
    "Banco do Brasil": "Banco do Brasil",
    "Pluxee": "Pluxee",
}


def resolver_conta(banco_csv: str, meio_pagamento_csv: str) -> str:
    """Qual conta (chave em CONTAS) uma linha do CSV pertence. BTG é o
    único banco que mistura 2 contas reais numa coluna só: cartão de
    crédito quando o meio de pagamento é 'Cartão de Crédito', corrente
    pra tudo mais (Pix, Crédito em Conta) que passou por lá."""
    if banco_csv == "BTG":
        return BTG_CARTAO if meio_pagamento_csv == "Cartão de Crédito" else BTG_CORRENTE
    try:
        return _BANCO_CSV_PARA_CONTA[banco_csv]
    except KeyError:
        raise ValueError(f"Banco não mapeado no CSV: {banco_csv!r}") from None
