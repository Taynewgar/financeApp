from datetime import date

from app.services.fatura import calcular_fatura_referencia, somar_meses


def test_compra_antes_do_fechamento_entra_no_ciclo_do_mes():
    # fechamento dia 8: compra em 5/ago entra na fatura que fecha em 8/ago
    assert calcular_fatura_referencia(date(2026, 8, 5), dia_fechamento=8) == date(2026, 8, 8)


def test_compra_no_dia_do_fechamento_entra_no_ciclo_do_mes():
    assert calcular_fatura_referencia(date(2026, 8, 8), dia_fechamento=8) == date(2026, 8, 8)


def test_compra_depois_do_fechamento_entra_no_proximo_ciclo():
    assert calcular_fatura_referencia(date(2026, 8, 9), dia_fechamento=8) == date(2026, 9, 8)


def test_fechamento_em_dezembro_vira_janeiro_do_ano_seguinte():
    assert calcular_fatura_referencia(date(2026, 12, 20), dia_fechamento=8) == date(2027, 1, 8)


def test_dia_de_fechamento_alem_do_mes_e_ajustado():
    # fechamento configurado como 31: fevereiro não tem, ajusta pro último dia
    assert calcular_fatura_referencia(date(2026, 2, 27), dia_fechamento=31) == date(2026, 2, 28)


def test_somar_meses_ajusta_dia_em_mes_mais_curto():
    assert somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_somar_meses_atravessa_o_ano():
    assert somar_meses(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_somar_zero_meses_retorna_a_mesma_data():
    assert somar_meses(date(2026, 5, 10), 0) == date(2026, 5, 10)
