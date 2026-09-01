"""Cálculo de fatura por ciclo de fechamento (cartão de crédito) e de datas
de parcelas — não por mês civil, para não perder compras próximas ao
fechamento (o problema real que motivou essa feature)."""
from __future__ import annotations

import calendar
from datetime import date


def calcular_fatura_referencia(data_compra: date, dia_fechamento: int) -> date:
    """Retorna a data de fechamento do ciclo ao qual a compra pertence.

    Compras até o dia de fechamento (inclusive) entram no ciclo que fecha
    naquele dia; depois disso, entram no ciclo seguinte. Um dia de
    fechamento que não existe no mês (ex.: 31 em fevereiro) é ajustado para
    o último dia do mês.
    """
    fechamento_deste_mes = _data_fechamento(data_compra.year, data_compra.month, dia_fechamento)
    if data_compra <= fechamento_deste_mes:
        return fechamento_deste_mes
    ano, mes = _proximo_mes(data_compra.year, data_compra.month)
    return _data_fechamento(ano, mes, dia_fechamento)


def somar_meses(data_base: date, meses: int) -> date:
    """Soma N meses a uma data, ajustando o dia se o mês de destino for
    mais curto (ex.: 31/01 + 1 mês -> 28/02 ou 29/02)."""
    total = data_base.month - 1 + meses
    ano = data_base.year + total // 12
    mes = total % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia)
    return date(ano, mes, dia)


def _data_fechamento(ano: int, mes: int, dia_fechamento: int) -> date:
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia_fechamento, ultimo_dia))


def _proximo_mes(ano: int, mes: int) -> tuple[int, int]:
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)
