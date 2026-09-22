"""Projeção virtual de lançamentos recorrentes (despesa fixa: aluguel,
assinaturas — decisão 2026-09-22, ver docs/backlog.md). Nada é gravado em
transacoes até o mês ser confirmado (POST
/lancamentos-recorrentes/{id}/confirmar) — essas funções só calculam datas
e "qual mês ainda falta confirmar", nunca escrevem nada."""
from __future__ import annotations

import calendar
from datetime import date

from .fatura import somar_meses

# trava defensiva contra loop sem fim (mesmo espírito de
# _MESES_MAXIMO_NA_EVOLUCAO em dashboard.py/estrutura_custo.py) — nenhum
# recorrente de verdade fica 6 anos sem ser confirmado nem uma vez
_MESES_MAXIMO_PROCURANDO_PENDENCIA = 72


def data_ocorrencia(vigencia_mes: date, dia_mes: int) -> date:
    """Dia `dia_mes` do mês de `vigencia_mes`, ajustado pro último dia do
    mês se ele for mais curto (ex.: dia_mes=31 em fevereiro -> 28 ou 29)."""
    ultimo_dia = calendar.monthrange(vigencia_mes.year, vigencia_mes.month)[1]
    return date(vigencia_mes.year, vigencia_mes.month, min(dia_mes, ultimo_dia))


def proxima_ocorrencia_pendente(recorrente: dict, meses_confirmados: set[str]) -> date | None:
    """Primeiro mês (a partir de data_inicio, andando pra frente) que ainda
    não tem transação confirmada vinculada a este recorrente — pode ser um
    mês já passado, se ficou pendente. `meses_confirmados` é o conjunto de
    vigencia_mes (isoformat, primeiro dia do mês) já confirmados DESTE
    recorrente. None se não há mais nenhuma ocorrência possível (passou de
    data_fim, ou nada pendente dentro da janela de busca)."""
    data_inicio = recorrente["data_inicio"]
    if isinstance(data_inicio, str):
        data_inicio = date.fromisoformat(data_inicio)
    data_fim = recorrente.get("data_fim")
    if isinstance(data_fim, str):
        data_fim = date.fromisoformat(data_fim)

    mes_atual = date(data_inicio.year, data_inicio.month, 1)
    for _ in range(_MESES_MAXIMO_PROCURANDO_PENDENCIA):
        if data_fim and mes_atual > date(data_fim.year, data_fim.month, 1):
            return None
        if mes_atual.isoformat() not in meses_confirmados:
            return mes_atual
        mes_atual = somar_meses(mes_atual, 1)
    return None
