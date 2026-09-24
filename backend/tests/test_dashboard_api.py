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


def test_aplicacao_e_retirada_sem_caixinha_compoe_investimentos_nao_reservas(client):
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
    # sem caixinha_id — é investimento, não reserva (mesma distinção de estrutura_custo.py)
    assert resposta["investimentos"] == 300
    assert resposta["reservas"] == 0


def test_aplicacao_e_retirada_com_caixinha_compoe_reservas_nao_investimentos(client):
    conta = _conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Emergência"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 800,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 300,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["reservas"] == 500
    assert resposta["investimentos"] == 0


def test_reservas_e_investimentos_no_mesmo_mes_nao_se_misturam(client):
    conta_investimento = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    conta_corrente = _conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Viagem"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1000,
            "tipo_movimento": "aplicacao",
            "conta_id": conta_investimento["id"],
            "estrutura_custo": "investimentos",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 100,
            "tipo_movimento": "aplicacao",
            "conta_id": conta_corrente["id"],
            "caixinha_id": caixinha["id"],
        },
    )

    resposta = client.get("/dashboard/mensal/2026-09-01").json()
    assert resposta["investimentos"] == 1000
    assert resposta["reservas"] == 100


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


def test_evolucao_busca_transacoes_do_periodo_em_lote_nao_por_mes(client, db_store):
    """Perf (mesmo fix de estrutura_custo.evolucao_orcamento, Rodada
    2026-09-22): antes era 1 SELECT em transacoes POR MÊS do período —
    ~O(meses) idas e voltas sequenciais ao Supabase. Agora é 1 SELECT pro
    período inteiro, agrupado em memória. Conta quantas vezes
    `db.table(...)` é chamado numa requisição de 6 meses — tem que ficar
    constante (1), não crescer com a quantidade de meses."""
    from app.auth import get_db
    from app.main import app

    from .fakes import FakeSupabaseClient

    conta = _conta(client)
    categoria_id = _categoria(client)
    for mes in range(1, 7):
        client.post(
            "/transacoes",
            json={
                "data_compra": f"2026-{mes:02d}-05",
                "valor": 700,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria_id,
                "estrutura_custo": "variavel",
                "meio_pagamento": "pix",
            },
        )

    class _ContadorClient:
        def __init__(self, store):
            self._inner = FakeSupabaseClient(store)
            self.chamadas: list[str] = []

        def table(self, nome):
            self.chamadas.append(nome)
            return self._inner.table(nome)

    contador = _ContadorClient(db_store)
    app.dependency_overrides[get_db] = lambda: contador
    try:
        resposta = client.get("/dashboard/evolucao", params={"inicio": "2026-01-01", "fim": "2026-06-01"})
    finally:
        app.dependency_overrides[get_db] = lambda: FakeSupabaseClient(db_store)

    assert resposta.status_code == 200
    assert len(resposta.json()["meses"]) == 6
    # sem o fix seriam pelo menos 6 (1 × 6 meses)
    assert contador.chamadas == ["transacoes"]


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


def _recorrente(client, conta_id, categoria_id, **extra):
    payload = {
        "descricao": "Aluguel",
        "valor": 1500,
        "dia_mes": 5,
        "tipo_movimento": "despesa",
        "conta_id": conta_id,
        "categoria_id": categoria_id,
        "estrutura_custo": "fixo",
        "meio_pagamento": "boleto",
        "data_inicio": "2026-01-01",
    }
    payload.update(extra)
    return client.post("/lancamentos-recorrentes", json=payload).json()


def test_compromissos_futuros_inclui_recorrente_pendente(client):
    conta = _conta(client)
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    _recorrente(client, conta["id"], categoria["id"])

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert len(resposta) == 1
    assert resposta[0]["tipo"] == "recorrente"
    assert resposta[0]["descricao"] == "Aluguel"
    assert resposta[0]["data_compra"] == "2026-01-05"  # mês de data_inicio, ainda não confirmado
    assert resposta[0]["parcela_atual"] is None


def test_compromissos_futuros_avanca_apos_confirmar(client):
    conta = _conta(client)
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    recorrente = _recorrente(client, conta["id"], categoria["id"])
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-01-01"})

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert len(resposta) == 1
    assert resposta[0]["data_compra"] == "2026-02-05"  # janeiro confirmado, próxima pendência é fevereiro


def test_compromissos_futuros_recorrente_inativo_nao_aparece(client):
    conta = _conta(client)
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    recorrente = _recorrente(client, conta["id"], categoria["id"])
    client.patch(f"/lancamentos-recorrentes/{recorrente['id']}/ativo", params={"ativo": False})

    assert client.get("/dashboard/compromissos-futuros").json() == []


def test_compromissos_futuros_mistura_parcela_e_recorrente_ordenado_por_data(client):
    cartao = _cartao(client)
    categoria_cartao = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    daqui_a_1_mes = date.today().replace(day=1) + timedelta(days=45)
    client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 1000,
            "parcela_total": 4,
            "data_primeira_parcela": daqui_a_1_mes.isoformat(),
            "conta_id": cartao["id"],
            "categoria_id": categoria_cartao["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
    )
    conta = _conta(client)
    categoria_aluguel = client.post("/categorias", json={"nome": "Aluguel"}).json()
    _recorrente(client, conta["id"], categoria_aluguel["id"])  # pendência de 2026-01-05, bem mais antiga

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert [r["tipo"] for r in resposta] == ["recorrente", "parcela"]
    assert resposta[0]["data_compra"] < resposta[1]["data_compra"]


def test_resumo_periodo_soma_todas_as_transacoes_do_intervalo(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-07-05", "valor": 1000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 1000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 600,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    # fora do intervalo pedido — não pode entrar na soma
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 999, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    resposta = client.get("/dashboard/resumo-periodo", params={"inicio": "2026-07-01", "fim": "2026-08-31"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["inicio"] == "2026-07-01"
    assert corpo["fim"] == "2026-08-01"
    assert corpo["receitas"] == 2000
    assert corpo["despesas_brutas"] == 600
    # taxa recalculada sobre o total do período, não a média dos meses
    assert corpo["taxa_poupanca"] == 70.0  # (2000-600)/2000*100


def test_resumo_periodo_com_fim_antes_de_inicio_retorna_422(client):
    resposta = client.get("/dashboard/resumo-periodo", params={"inicio": "2026-09-01", "fim": "2026-08-01"})
    assert resposta.status_code == 422


def test_primeiro_mes_sem_transacoes_retorna_none(client):
    resposta = client.get("/dashboard/primeiro-mes")
    assert resposta.status_code == 200
    assert resposta.json()["vigencia_mes"] is None


def test_primeiro_mes_retorna_mes_do_lancamento_mais_antigo(client):
    conta = _conta(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2024-03-17", "valor": 100, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2025-01-05", "valor": 100, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    resposta = client.get("/dashboard/primeiro-mes").json()
    assert resposta["vigencia_mes"] == "2024-03-01"


def test_primeiro_mes_de_outro_usuario_nao_conta(client, current_user):
    conta = _conta(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2024-03-17", "valor": 100, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    current_user["id"] = OUTRO_USUARIO
    resposta = client.get("/dashboard/primeiro-mes").json()
    assert resposta["vigencia_mes"] is None


def test_despesas_por_categoria_agrupa_por_categoria_pai_com_percentual(client):
    conta = _conta(client)
    moradia = client.post("/categorias", json={"nome": "Moradia"}).json()["id"]
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()["id"]
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 800,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": moradia,
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 200,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": lazer,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/dashboard/despesas-por-categoria/2026-09-01")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 2
    # ordenado desc por valor
    assert corpo[0]["categoria_nome"] == "Moradia"
    assert corpo[0]["valor"] == 800
    assert corpo[0]["percentual"] == 80.0
    assert corpo[1]["categoria_nome"] == "Lazer"
    assert corpo[1]["percentual"] == 20.0


def test_despesas_por_categoria_soma_2_lancamentos_da_mesma_categoria(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    for valor in (100, 50):
        client.post(
            "/transacoes",
            json={
                "data_compra": "2026-09-05",
                "valor": valor,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria_id,
                "estrutura_custo": "variavel",
                "meio_pagamento": "pix",
            },
        )

    resposta = client.get("/dashboard/despesas-por-categoria/2026-09-01").json()
    assert len(resposta) == 1
    assert resposta[0]["valor"] == 150
    assert resposta[0]["percentual"] == 100.0


def test_despesas_por_categoria_sem_despesas_retorna_lista_vazia(client):
    resposta = client.get("/dashboard/despesas-por-categoria/2026-09-01").json()
    assert resposta == []


def test_despesas_por_categoria_periodo_soma_varios_meses(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    for data, valor in [("2026-07-05", 100), ("2026-08-05", 200), ("2026-09-05", 300)]:
        client.post(
            "/transacoes",
            json={
                "data_compra": data,
                "valor": valor,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria_id,
                "estrutura_custo": "variavel",
                "meio_pagamento": "pix",
            },
        )

    resposta = client.get(
        "/dashboard/despesas-por-categoria-periodo", params={"inicio": "2026-07-01", "fim": "2026-09-01"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["valor"] == 600
    assert corpo[0]["percentual"] == 100.0


def test_despesas_por_categoria_periodo_nao_inclui_mes_fora_do_intervalo(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-06-05",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get(
        "/dashboard/despesas-por-categoria-periodo", params={"inicio": "2026-07-01", "fim": "2026-09-01"}
    ).json()
    assert len(resposta) == 1
    assert resposta[0]["valor"] == 100


def test_despesas_por_categoria_periodo_fim_antes_de_inicio_retorna_422(client):
    resposta = client.get(
        "/dashboard/despesas-por-categoria-periodo", params={"inicio": "2026-09-01", "fim": "2026-07-01"}
    )
    assert resposta.status_code == 422


def test_despesas_por_categoria_periodo_sem_despesas_retorna_lista_vazia(client):
    resposta = client.get(
        "/dashboard/despesas-por-categoria-periodo", params={"inicio": "2026-07-01", "fim": "2026-09-01"}
    ).json()
    assert resposta == []


def _lancar_despesa_com_subcategoria(client, conta, categoria_id, subcategoria_id, valor, data="2026-09-05"):
    client.post(
        "/transacoes",
        json={
            "data_compra": data,
            "valor": valor,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )


def test_despesas_por_subcategoria_agrupa_e_ordena_por_valor(client):
    conta = _conta(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()["id"]
    hortifruti = client.post("/subcategorias", json={"categoria_id": mercado, "nome": "Hortifruti"}).json()["id"]
    acougue = client.post("/subcategorias", json={"categoria_id": mercado, "nome": "Açougue"}).json()["id"]
    _lancar_despesa_com_subcategoria(client, conta, mercado, hortifruti, 300)
    _lancar_despesa_com_subcategoria(client, conta, mercado, acougue, 100)

    resposta = client.get("/dashboard/despesas-por-subcategoria/2026-09-01").json()
    assert len(resposta) == 2
    assert resposta[0]["subcategoria_nome"] == "Hortifruti"
    assert resposta[0]["percentual"] == 75.0
    assert resposta[1]["subcategoria_nome"] == "Açougue"


def test_despesas_por_subcategoria_sem_subcategoria_agrupa_em_bucket_proprio(client):
    conta = _conta(client)
    categoria_id = _categoria(client)
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/dashboard/despesas-por-subcategoria/2026-09-01").json()
    assert len(resposta) == 1
    assert resposta[0]["subcategoria_id"] is None
    assert resposta[0]["subcategoria_nome"] == "Sem subcategoria"


def test_despesas_por_subcategoria_filtra_por_categoria_pai(client):
    conta = _conta(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()["id"]
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()["id"]
    hortifruti = client.post("/subcategorias", json={"categoria_id": mercado, "nome": "Hortifruti"}).json()["id"]
    cinema = client.post("/subcategorias", json={"categoria_id": lazer, "nome": "Cinema"}).json()["id"]
    _lancar_despesa_com_subcategoria(client, conta, mercado, hortifruti, 100)
    _lancar_despesa_com_subcategoria(client, conta, lazer, cinema, 200)

    resposta = client.get(
        "/dashboard/despesas-por-subcategoria/2026-09-01", params={"categoria_id": mercado}
    ).json()
    assert len(resposta) == 1
    assert resposta[0]["subcategoria_nome"] == "Hortifruti"
    assert resposta[0]["percentual"] == 100.0


def test_despesas_por_subcategoria_periodo_soma_varios_meses(client):
    conta = _conta(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()["id"]
    hortifruti = client.post("/subcategorias", json={"categoria_id": mercado, "nome": "Hortifruti"}).json()["id"]
    _lancar_despesa_com_subcategoria(client, conta, mercado, hortifruti, 100, data="2026-07-05")
    _lancar_despesa_com_subcategoria(client, conta, mercado, hortifruti, 200, data="2026-08-05")

    resposta = client.get(
        "/dashboard/despesas-por-subcategoria-periodo", params={"inicio": "2026-07-01", "fim": "2026-09-01"}
    ).json()
    assert len(resposta) == 1
    assert resposta[0]["valor"] == 300


def test_despesas_por_subcategoria_periodo_fim_antes_de_inicio_retorna_422(client):
    resposta = client.get(
        "/dashboard/despesas-por-subcategoria-periodo", params={"inicio": "2026-09-01", "fim": "2026-07-01"}
    )
    assert resposta.status_code == 422
