"""Teto em R$ de um bucket do orçamento: a fatia percentual do que foi
efetivamente destinado a orçamento (receita_base × percentual_geral).

É o teto "puro", sem considerar acúmulo de mês anterior — usado como está
para validar a soma dos itens de um bucket (o saldo_anterior de cada item
cancela nos dois lados dessa conta, então não precisa entrar aqui). Quem
precisa do acúmulo (o pool entre buckets em estrutura_custo.py) soma o
saldo_anterior por fora, depois de chamar esta função.
"""

_CAMPO_LIMITE = {
    "custos_fixos": "limite_custos_fixos",
    "custos_variaveis": "limite_custos_variaveis",
    "sazonalidades": "limite_sazonalidades",
    "investimentos": "limite_investimentos",
}


def calcular_teto_bucket(orcamento: dict, bucket: str) -> float:
    base_orcada = orcamento["receita_base"] * orcamento["percentual_geral"] / 100
    limite = orcamento[_CAMPO_LIMITE[bucket]]
    return round(base_orcada * limite / 100, 2)
