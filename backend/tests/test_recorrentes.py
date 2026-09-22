from datetime import date

from app.services.recorrentes import data_ocorrencia, proxima_ocorrencia_pendente


def test_data_ocorrencia_usa_o_dia_pedido():
    assert data_ocorrencia(date(2026, 9, 1), 15) == date(2026, 9, 15)


def test_data_ocorrencia_ajusta_dia_alem_do_mes():
    # fevereiro de 2026 não é bissexto — dia 31 vira 28
    assert data_ocorrencia(date(2026, 2, 1), 31) == date(2026, 2, 28)


def test_data_ocorrencia_ajusta_pro_ultimo_dia_em_ano_bissexto():
    assert data_ocorrencia(date(2028, 2, 1), 31) == date(2028, 2, 29)


def _recorrente(data_inicio: str, data_fim: str | None = None) -> dict:
    return {"data_inicio": data_inicio, "data_fim": data_fim}


def test_proxima_ocorrencia_pendente_e_o_mes_de_inicio_sem_nenhum_confirmado():
    assert proxima_ocorrencia_pendente(_recorrente("2026-09-01"), set()) == date(2026, 9, 1)


def test_proxima_ocorrencia_pendente_pula_meses_ja_confirmados():
    confirmados = {"2026-09-01", "2026-10-01"}
    assert proxima_ocorrencia_pendente(_recorrente("2026-09-01"), confirmados) == date(2026, 11, 1)


def test_proxima_ocorrencia_pendente_retorna_mes_atrasado_nao_confirmado_no_meio():
    # setembro confirmado, outubro não — mesmo já tendo novembro também
    # confirmado, outubro é o que falta
    confirmados = {"2026-09-01", "2026-11-01"}
    assert proxima_ocorrencia_pendente(_recorrente("2026-09-01"), confirmados) == date(2026, 10, 1)


def test_proxima_ocorrencia_pendente_none_depois_de_data_fim_toda_confirmada():
    confirmados = {"2026-09-01", "2026-10-01"}
    assert proxima_ocorrencia_pendente(_recorrente("2026-09-01", "2026-10-01"), confirmados) is None


def test_proxima_ocorrencia_pendente_ainda_aparece_se_dentro_de_data_fim():
    assert proxima_ocorrencia_pendente(_recorrente("2026-09-01", "2026-11-01"), set()) == date(2026, 9, 1)
