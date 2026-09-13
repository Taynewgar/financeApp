from datetime import date, timedelta

from .conftest import OUTRO_USUARIO


def _conta(client):
    return client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()


def _categoria(client):
    return client.post("/categorias", json={"nome": "Categoria Teste"}).json()["id"]


def _cartao(client):
    return client.post(
        "/contas", json={"nome": "Cartão", "tipo_conta": "cartao_credito"}
    ).json()


def test_mes_sem_transacoes_retorna_zeros_e_taxa_poupanca_none(client):
    resposta = client.get("/dashboard/mensal/2026-09-01")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["receitas"] == 0
    assert corpo["resultado_saude"] == 0
    assert corpo["taxa_poupanca"] is None


def test_receita_e_despesa_simples_calculam_resultado(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 5000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 3000,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["receitas"] == 5000
    assert resposta["despesas_brutas"] == 3000
    assert resposta["despesas_liquidas"] == 3000
    assert resposta["resultado_fluxo_caixa"] == 2000
    assert resposta["resultado_saude"] == 2000
    assert resposta["taxa_poupanca"] == 40.0  # 2000 / 5000 * 100


def test_estorno_vinculado_reduz_despesa_liquida_mas_nao_conta_como_receita(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    despesa = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    ).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 100,
            "tipo_movimento": "estorno",
            "conta_id": conta["id"],
            "ajuste_de_transacao_id": despesa["id"],
        },
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["despesas_brutas"] == 300
    assert resposta["ajustes_vinculados"] == 100
    assert resposta["despesas_liquidas"] == 200
    assert resposta["ajustes_nao_vinculados"] == 0
    # fluxo de caixa ignora o ajuste — só olha receita/despesa brutas
    assert resposta["resultado_fluxo_caixa"] == -300
    # saúde já desconta o estorno da despesa, sem contá-lo como receita nova
    assert resposta["resultado_saude"] == -200


def test_estorno_nao_vinculado_conta_como_receita_extra_na_saude(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-10", "valor": 50, "tipo_movimento": "ressarcimento", "conta_id": conta["id"]},
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["ajustes_nao_vinculados"] == 50
    assert resposta["despesas_liquidas"] == 300  # não vinculado não abate despesa nenhuma
    assert resposta["resultado_saude"] == -250  # (0 + 50) - 300
    assert resposta["resultado_fluxo_caixa"] == -300  # ajuste solto não entra no fluxo de caixa


def test_aplicacao_e_retirada_compoe_reservas(client):
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 200,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["aplicacoes"] == 500
    assert resposta["retiradas"] == 200
    assert resposta["reservas"] == 300


def test_transacao_fora_do_mes_nao_entra_no_resumo(client):
    conta = _conta(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-08-31", "valor": 999, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-10-01", "valor": 999, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["receitas"] == 0


def test_transacao_de_outro_usuario_nao_entra_no_resumo(client, current_user):
    conta = _conta(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 999, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    current_user["id"] = OUTRO_USUARIO
    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["receitas"] == 0


def test_evolucao_acumula_resultado_entre_meses(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 1000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 400,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 1000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 700,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/dashboard/evolucao", params={"inicio": "2026-08-01", "fim": "2026-09-30"})
    assert resposta.status_code == 200
    meses = resposta.json()["meses"]
    assert len(meses) == 2
    assert meses[0]["resultado_saude"] == 600
    assert meses[0]["resultado_saude_acumulado"] == 600
    assert meses[1]["resultado_saude"] == 300
    assert meses[1]["resultado_saude_acumulado"] == 900


def test_evolucao_com_fim_antes_de_inicio_retorna_422(client):
    resposta = client.get("/dashboard/evolucao", params={"inicio": "2026-09-01", "fim": "2026-08-01"})
    assert resposta.status_code == 422


def test_evolucao_com_intervalo_maior_que_5_anos_retorna_422(client):
    resposta = client.get("/dashboard/evolucao", params={"inicio": "2020-01-01", "fim": "2026-09-01"})
    assert resposta.status_code == 422


def test_patrimonio_soma_aplicacoes_menos_retiradas_por_caixinha(client):
    conta = _conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Viagem"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 200,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )

    resposta = client.get("/dashboard/patrimonio/2026-09-01")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo == [{"id": caixinha["id"], "nome": "Viagem", "saldo": 300}]


def test_patrimonio_ignora_movimentos_depois_do_fim_do_mes_selecionado(client):
    conta = _conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Viagem"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-01",
            "valor": 100,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )

    resposta = client.get("/dashboard/patrimonio/2026-09-01").json()
    assert resposta[0]["saldo"] == 500  # movimento de outubro não conta pro saldo de setembro

    resposta_outubro = client.get("/dashboard/patrimonio/2026-10-01").json()
    assert resposta_outubro[0]["saldo"] == 600  # já acumula os dois meses


def test_patrimonio_nao_lista_caixinha_inativa(client):
    caixinha = client.post("/caixinhas", json={"nome": "Antiga"}).json()
    client.patch(f"/caixinhas/{caixinha['id']}/ativo", params={"ativo": False})

    resposta = client.get("/dashboard/patrimonio/2026-09-01").json()
    assert resposta == []


def test_patrimonio_de_outro_usuario_nao_aparece(client, current_user):
    client.post("/caixinhas", json={"nome": "Viagem"})

    current_user["id"] = OUTRO_USUARIO
    resposta = client.get("/dashboard/patrimonio/2026-09-01").json()
    assert resposta == []


def test_compromissos_futuros_retorna_proxima_parcela_de_cada_grupo(client):
    cartao = _cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    daqui_a_1_mes = date.today().replace(day=1) + timedelta(days=45)  # cai bem no mês seguinte
    client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 1000,
            "parcela_total": 4,
            "data_primeira_parcela": daqui_a_1_mes.isoformat(),
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
    )

    resposta = client.get("/dashboard/compromissos-futuros")
    assert resposta.status_code == 200
    corpo = resposta.json()
    # só a próxima parcela em aberto aparece — não as 3 restantes do grupo
    assert len(corpo) == 1
    assert corpo[0]["descricao"] == "Notebook"
    assert corpo[0]["parcela_atual"] == 1
    assert corpo[0]["parcela_total"] == 4


def test_compromissos_futuros_ignora_parcela_ja_vencida(client):
    cartao = _cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Compra antiga",
            "valor_total": 100,
            "parcela_total": 2,
            "data_primeira_parcela": "2020-01-05",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
    )

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert resposta == []


def test_compromissos_futuros_ignora_lancamento_a_vista(client):
    conta = _conta(client)
    client.post(
        "/transacoes",
        json={
            "data_compra": (date.today() + timedelta(days=10)).isoformat(),
            "valor": 100,
            "tipo_movimento": "receita",
            "conta_id": conta["id"],
        },
    )

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert resposta == []


def test_compromissos_futuros_respeita_limite(client):
    cartao = _cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    daqui_a_1_mes = date.today().replace(day=1) + timedelta(days=45)
    for i in range(3):
        client.post(
            "/transacoes/parceladas",
            json={
                "descricao": f"Compra {i}",
                "valor_total": 100,
                "parcela_total": 2,
                "data_primeira_parcela": daqui_a_1_mes.isoformat(),
                "conta_id": cartao["id"],
                "categoria_id": categoria["id"],
                "estrutura_custo": "variavel",
                "meio_pagamento": "cartao_credito",
            },
        )

    resposta = client.get("/dashboard/compromissos-futuros", params={"limite": 2}).json()
    assert len(resposta) == 2
