"""Duas leituras financeiras, herdadas do app original (core/data_processor.py):

* fluxo de caixa (bruto): o que de fato entrou/saiu, sem nenhum ajuste.
* saúde financeira (líquida): um estorno/ressarcimento VINCULADO a uma
  despesa (ajuste_de_transacao_id preenchido) não é uma nova receita — ele
  só desfaz parte daquela despesa, então reduz despesas_liquidas. Um ajuste
  SOLTO (sem vínculo) não desfaz nada específico, então conta como receita
  extra na leitura de saúde. No fluxo de caixa os dois tipos de ajuste são
  ignorados (só receita/despesa brutas importam ali).

Compartilhado entre o Dashboard (resumo por mês) e a Busca de Lançamentos
(resumo do que bate com os filtros aplicados) — é a mesma conta, só muda
de onde vêm as transações somadas.
"""
from typing import Any


def calcular_resumo(transacoes: list[dict[str, Any]]) -> dict[str, Any]:
    receitas = despesas_brutas = ajustes_vinculados = ajustes_nao_vinculados = 0.0
    aplicacoes = retiradas = 0.0
    for t in transacoes:
        valor = t["valor"]
        tipo = t["tipo_movimento"]
        if tipo == "receita":
            receitas += valor
        elif tipo == "despesa":
            despesas_brutas += valor
        elif tipo in ("estorno", "ressarcimento"):
            if t.get("ajuste_de_transacao_id"):
                ajustes_vinculados += valor
            else:
                ajustes_nao_vinculados += valor
        elif tipo == "aplicacao":
            aplicacoes += valor
        elif tipo == "retirada":
            retiradas += valor

    despesas_liquidas = round(despesas_brutas - ajustes_vinculados, 2)
    receita_ajustada = round(receitas + ajustes_nao_vinculados, 2)
    resultado_saude = round(receita_ajustada - despesas_liquidas, 2)

    return {
        "receitas": round(receitas, 2),
        "despesas_brutas": round(despesas_brutas, 2),
        "despesas_liquidas": despesas_liquidas,
        "ajustes_vinculados": round(ajustes_vinculados, 2),
        "ajustes_nao_vinculados": round(ajustes_nao_vinculados, 2),
        "aplicacoes": round(aplicacoes, 2),
        "retiradas": round(retiradas, 2),
        "reservas": round(aplicacoes - retiradas, 2),
        "resultado_fluxo_caixa": round(receitas - despesas_brutas, 2),
        "resultado_saude": resultado_saude,
        "taxa_poupanca": round(resultado_saude / receita_ajustada * 100, 2) if receita_ajustada else None,
        # uso interno de quem acumula entre períodos (ex: dashboard/evolucao); nunca sai numa resposta
        "_receita_ajustada": receita_ajustada,
    }
