def _bucket(resposta, nome):
    return next(b for b in resposta.json()["buckets"] if b["bucket"] == nome)


def test_mes_sem_orcamento_e_sem_transacoes_retorna_todos_buckets_zerados(client):
    resposta = client.get("/estrutura-custo/2026-09-01")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["orcamento_id"] is None
    assert {b["bucket"] for b in corpo["buckets"]} == {
        "custos_fixos",
        "custos_variaveis",
        "sazonalidades",
        "investimentos",
        "reservas",
        "sem_estrutura",
    }
    assert all(b["orcado"] == 0 and b["realizado"] == 0 and b["itens"] == [] for b in corpo["buckets"])
    assert corpo["pool_despesas"] is None
    assert corpo["piso_investimentos"] is None


def test_aplicacao_em_caixinha_vai_para_bucket_reservas_nao_investimentos(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    caixinha = client.post("/caixinhas", json={"nome": "Reserva de Emergência"}).json()
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

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert _bucket(resposta, "reservas")["realizado"] == 500
    assert _bucket(resposta, "investimentos")["realizado"] == 0


def test_despesa_com_estrutura_fixo_aparece_em_custos_fixos(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert fixos["realizado"] == 1500
    assert fixos["orcado"] == 0
    assert fixos["itens"][0]["categoria_id"] == categoria["id"]


def test_duas_despesas_da_mesma_subcategoria_no_mes_somam_no_realizado(client):
    """Regressão da migração pra RPC de agregação (2026-09-25,
    saldo_transacoes_agregado): 2 lançamentos que caem no mesmo grupo
    (mesma categoria/subcategoria/conta/estrutura_custo/tipo_movimento no
    mesmo mês) precisam ser SOMADOS pelo Postgres antes de chegar em
    Python — não podem aparecer como 2 linhas concorrentes nem sobrescrever
    uma a outra."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    subcategoria = client.post(
        "/subcategorias", json={"nome": "Aluguel", "categoria_id": categoria["id"]}
    ).json()
    for valor in (1200, 300):
        client.post(
            "/transacoes",
            json={
                "data_compra": "2026-09-05",
                "valor": valor,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria["id"],
                "subcategoria_id": subcategoria["id"],
                "estrutura_custo": "fixo",
                "meio_pagamento": "pix",
            },
        )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert fixos["realizado"] == 1500
    assert fixos["itens"][0]["realizado"] == 1500


# test_despesa_sem_estrutura_custo_cai_em_sem_estrutura removido: seu
# premissa (despesa sem estrutura_custo) não é mais alcançável pela API —
# categoria_id/estrutura_custo/meio_pagamento agora são obrigatórios para
# despesa (ver _check_campos_obrigatorios em routers/transacoes.py). O
# bucket "sem_estrutura" continua existindo no código (diagnóstico de dados
# legados) e sua presença na lista de buckets segue coberta por
# test_mes_sem_orcamento_e_sem_transacoes_retorna_todos_buckets_zerados.


def test_aplicacao_aparece_em_investimentos(client):
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    investimentos = _bucket(resposta, "investimentos")
    assert investimentos["realizado"] == 300
    assert investimentos["itens"][0]["conta_id"] == conta["id"]


def test_retirada_reduz_realizado_de_investimentos(client):
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-15",
            "valor": 100,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert _bucket(resposta, "investimentos")["realizado"] == 200


def test_estorno_reduz_realizado_do_bucket(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    despesa = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 200,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    ).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 50,
            "tipo_movimento": "estorno",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "ajuste_de_transacao_id": despesa["id"],
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert _bucket(resposta, "custos_variaveis")["realizado"] == 150


def test_orcado_aparece_mesmo_sem_realizado(client):
    categoria = client.post("/categorias", json={"nome": "Streaming"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-09-01", "receita_base": 100000, "percentual_geral": 100}
    ).json()
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria["id"], "orcamento_mensal": 60},
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert resposta.json()["orcamento_id"] == orcamento["id"]
    variaveis = _bucket(resposta, "custos_variaveis")
    assert variaveis["orcado"] == 60
    assert variaveis["realizado"] == 0


def test_categorias_diferentes_nao_se_misturam_no_mesmo_bucket(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    aluguel = client.post("/categorias", json={"nome": "Aluguel"}).json()
    internet = client.post("/categorias", json={"nome": "Internet"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1200,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": aluguel["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": internet["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert fixos["realizado"] == 1300
    valores_por_categoria = {i["categoria_id"]: i["realizado"] for i in fixos["itens"]}
    assert valores_por_categoria == {aluguel["id"]: 1200, internet["id"]: 100}


def test_subcategoria_aparece_como_item_proprio_nao_agregado_na_categoria(client):
    """Lançamento com subcategoria sempre grava a categoria pai junto
    (NovoLancamento.tsx) — a chave do item tem que priorizar a
    subcategoria, senão ela nunca aparece separada do "Geral"."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    subcategoria = client.post(
        "/subcategorias", json={"categoria_id": categoria["id"], "nome": "Aluguel"}
    ).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "subcategoria_id": subcategoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert len(fixos["itens"]) == 1
    item = fixos["itens"][0]
    assert item["subcategoria_id"] == subcategoria["id"]
    assert item["categoria_id"] is None
    assert item["realizado"] == 1500


def test_transacao_fora_do_mes_nao_entra_no_calculo(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-31",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-01",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert _bucket(resposta, "custos_fixos")["realizado"] == 0


def test_receita_nao_entra_no_calculo_de_nenhum_bucket(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 5000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert all(b["realizado"] == 0 for b in resposta.json()["buckets"])


# ── pool de despesas e piso de investimentos (regra 2) ──────────────────────
# mesmo exemplo: renda 15000, percentual_geral 90% → teto_fixos=5400,
# teto_variaveis=3375, teto_sazonalidades=1350 (pool=10125), teto_investimentos=3375


def _criar_orcamento_do_exemplo(client, vigencia_mes="2026-09-01"):
    return client.post(
        "/orcamentos", json={"vigencia_mes": vigencia_mes, "receita_base": 15000, "percentual_geral": 90}
    ).json()


def _despesa(client, conta_id, valor, estrutura_custo, data="2026-09-05", categoria_id=None):
    if categoria_id is None:
        categoria_id = client.post("/categorias", json={"nome": "Categoria Teste"}).json()["id"]
    return client.post(
        "/transacoes",
        json={
            "data_compra": data,
            "valor": valor,
            "tipo_movimento": "despesa",
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "estrutura_custo": estrutura_custo,
            "meio_pagamento": "pix",
        },
    )


def test_pool_despesas_absorve_estouro_de_um_bucket_quando_outros_tem_folga(client):
    """O mesmo cenário da conversa: fixos estourou, variáveis e
    sazonalidades sobraram — o agregado dos 3 continua dentro do teto."""
    _criar_orcamento_do_exemplo(client)
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    # 1 categoria reaproveitada nas 3 despesas — categorias têm nome único
    # por usuário (categorias_user_id_nome_key), _despesa() criaria 3
    # "Categoria Teste" diferentes e a 2ª já bateria na constraint
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    _despesa(client, conta["id"], 5800, "fixo", categoria_id=categoria["id"])
    _despesa(client, conta["id"], 2500, "variavel", categoria_id=categoria["id"])
    _despesa(client, conta["id"], 1000, "sazonal", categoria_id=categoria["id"])

    resposta = client.get("/estrutura-custo/2026-09-01").json()
    assert _bucket(client.get("/estrutura-custo/2026-09-01"), "custos_fixos")["realizado"] == 5800  # estourou sozinho
    assert resposta["pool_despesas"]["teto"] == 10125
    assert resposta["pool_despesas"]["realizado"] == 9300
    assert resposta["pool_despesas"]["dentro_do_teto"] is True


def test_pool_despesas_estoura_quando_soma_total_passa_do_teto_agregado(client):
    _criar_orcamento_do_exemplo(client)
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    _despesa(client, conta["id"], 6000, "fixo", categoria_id=categoria["id"])
    _despesa(client, conta["id"], 3000, "variavel", categoria_id=categoria["id"])
    _despesa(client, conta["id"], 1500, "sazonal", categoria_id=categoria["id"])

    resposta = client.get("/estrutura-custo/2026-09-01").json()
    assert resposta["pool_despesas"]["realizado"] == 10500
    assert resposta["pool_despesas"]["dentro_do_teto"] is False


def test_pool_despesas_considera_saldo_anterior_do_envelope(client):
    """A sobra de setembro em custos_fixos amplia o teto agregado de
    outubro — não só o teto individual do bucket, o pool inteiro."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()

    setembro = _criar_orcamento_do_exemplo(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{setembro['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 700,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    client.post(f"/orcamentos/{setembro['id']}/proximo-mes")  # outubro nasce com saldo_anterior=300 no item de fixos

    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-05",
            "valor": 10200,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/estrutura-custo/2026-10-01").json()
    assert resposta["pool_despesas"]["teto"] == 10425  # 10125 (baseline) + 300 (saldo_anterior carregado)
    assert resposta["pool_despesas"]["realizado"] == 10200
    assert resposta["pool_despesas"]["dentro_do_teto"] is True  # sem o saldo_anterior, 10200 > 10125 estouraria

    item_aluguel = next(i for i in _bucket(client.get("/estrutura-custo/2026-10-01"), "custos_fixos")["itens"] if i["categoria_id"] == categoria["id"])
    assert item_aluguel["orcamento_mensal"] == 1000
    assert item_aluguel["saldo_anterior"] == 300
    assert item_aluguel["orcado"] == 1300  # orcamento_mensal + saldo_anterior, mesmo valor exposto antes


def test_piso_investimentos_meta_batida(client):
    _criar_orcamento_do_exemplo(client)
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 4000,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01").json()
    assert resposta["piso_investimentos"]["teto"] == 3375
    assert resposta["piso_investimentos"]["realizado"] == 4000
    assert resposta["piso_investimentos"]["meta_batida"] is True


def test_piso_investimentos_meta_nao_batida(client):
    _criar_orcamento_do_exemplo(client)
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 2000,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01").json()
    assert resposta["piso_investimentos"]["meta_batida"] is False


# ── tendência de orçado x realizado em vários meses (Rodada C, item 5) ──────


def test_evolucao_orcamento_soma_pool_e_calcula_percentual(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-09-01", "receita_base": 10000, "percentual_geral": 100}
    ).json()
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    _despesa(client, conta["id"], 800, "fixo", data="2026-09-05", categoria_id=categoria["id"])

    resposta = client.get("/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-09-01", "fim": "2026-09-01"})
    assert resposta.status_code == 200
    meses = resposta.json()["meses"]
    assert len(meses) == 1
    assert meses[0]["orcado"] == 1000
    assert meses[0]["realizado"] == 800
    assert meses[0]["percentual_executado"] == 80.0


def test_evolucao_orcamento_nao_inclui_investimentos_no_pool(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria_invest = client.post("/categorias", json={"nome": "Renda Fixa", "tipo": "investimento"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-09-01", "receita_base": 10000, "percentual_geral": 100}
    ).json()
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "investimentos", "categoria_id": categoria_invest["id"], "orcamento_mensal": 500},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "categoria_id": categoria_invest["id"],
            "estrutura_custo": "investimentos",
        },
    )

    resposta = client.get(
        "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-09-01", "fim": "2026-09-01"}
    ).json()
    assert resposta["meses"][0]["orcado"] == 0
    assert resposta["meses"][0]["realizado"] == 0


def test_evolucao_orcamento_mes_sem_orcamento_tem_percentual_nulo(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    _despesa(client, conta["id"], 300, "variavel", data="2026-09-05")

    resposta = client.get(
        "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-09-01", "fim": "2026-09-01"}
    ).json()
    mes = resposta["meses"][0]
    assert mes["orcado"] == 0
    assert mes["realizado"] == 300
    assert mes["percentual_executado"] is None


def test_evolucao_orcamento_varios_meses_retorna_um_ponto_por_mes(client):
    resposta = client.get(
        "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-07-01", "fim": "2026-09-01"}
    ).json()
    assert [m["vigencia_mes"] for m in resposta["meses"]] == ["2026-07-01", "2026-08-01", "2026-09-01"]


def test_evolucao_orcamento_compartilha_cache_de_saldo_entre_os_meses_do_periodo(client, monkeypatch):
    """Perf (v1, mecanismo em memória): garante que o loop passa o MESMO
    dict de cache pra _estrutura_custo_do_mes_em_lote em todos os meses do
    período, não um novo a cada iteração — evita refazer a subida da
    cadeia de saldo_anterior em memória mais de uma vez pro mesmo item+mês
    (ver saldo_anterior_em_lote). A perf de banco em si (v2: período
    inteiro em poucas queries, não 1 por mês) é coberta pelo teste
    seguinte."""
    import app.routers.estrutura_custo as estrutura_custo_router

    caches_vistos = []
    original = estrutura_custo_router._estrutura_custo_do_mes_em_lote

    def _espiao(mes_inicio, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo):
        caches_vistos.append(cache_saldo)
        return original(mes_inicio, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo)

    monkeypatch.setattr(estrutura_custo_router, "_estrutura_custo_do_mes_em_lote", _espiao)

    resposta = client.get(
        "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-01-01", "fim": "2026-04-01"}
    )

    assert resposta.status_code == 200
    assert len(caches_vistos) == 4  # 1 chamada por mês do período (jan-abr)
    assert all(cache is not None for cache in caches_vistos)
    assert all(cache is caches_vistos[0] for cache in caches_vistos)  # mesmo objeto em todos os meses


def test_evolucao_orcamento_busca_dados_do_periodo_em_lote_nao_por_mes(client, db_store):
    """Perf (v2, o que de fato resolveu "Gráficos continua lento" — Rodada
    2026-09-22): antes eram 3 SELECTs (orçamento, itens, transações) POR
    MÊS do período dentro de um loop Python — ~O(meses) idas e voltas
    sequenciais ao Supabase, cada uma com latência real de rede. Agora
    busca o período inteiro em poucas queries e agrupa em memória. Testa
    isso de verdade: conta quantas vezes `db.table(...)` é chamado numa
    requisição de 6 meses com orçamento encadeado (cadeia de
    saldo_anterior de verdade, não só meses vazios) — tem que ficar
    constante, não crescer com a quantidade de meses."""
    from app.auth import get_db
    from app.main import app

    from .fakes import FakeSupabaseClient

    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-01-01", "receita_base": 10000, "percentual_geral": 100}
    ).json()
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    # encadeia 6 meses via "gerar próximo mês" (jan-jun), mesma categoria
    # em todo mundo — é isso que faz a cadeia de saldo_anterior existir de
    # verdade (senão o teste passaria mesmo sem o fix, por falta de dado)
    for mes in range(1, 6):
        client.post(
            "/transacoes",
            json={
                "data_compra": f"2026-{mes:02d}-05",
                "valor": 700,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria["id"],
                "estrutura_custo": "fixo",
                "meio_pagamento": "pix",
            },
        )
        orcamento = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()

    class _ContadorClient:
        def __init__(self, store):
            self._inner = FakeSupabaseClient(store)
            self.chamadas: list[str] = []

        def table(self, nome):
            self.chamadas.append(nome)
            return self._inner.table(nome)

        def rpc(self, nome, params):
            self.chamadas.append(nome)
            return self._inner.rpc(nome, params)

    contador = _ContadorClient(db_store)
    app.dependency_overrides[get_db] = lambda: contador
    try:
        resposta = client.get(
            "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-01-01", "fim": "2026-06-01"}
        )
    finally:
        app.dependency_overrides[get_db] = lambda: FakeSupabaseClient(db_store)

    assert resposta.status_code == 200
    # 3 no total (orcamentos + orcamento_itens + transacoes), não 1 grupo
    # dessas por mês — sem o fix seriam pelo menos 18 (3 × 6 meses)
    assert contador.chamadas.count("orcamentos") == 1
    assert contador.chamadas.count("orcamento_itens") == 1
    assert contador.chamadas.count("saldo_transacoes_agregado") == 1
    assert len(contador.chamadas) == 3


def test_obter_um_mes_busca_dados_em_lote_nao_recalcula_cadeia_item_a_item(client, db_store):
    """Perf (Rodada 2026-09-24, item 22 do backlog — mesma classe de bug
    de test_evolucao_orcamento_busca_dados_do_periodo_em_lote_nao_por_mes,
    agora em obter(), a tela de Estrutura de Custo de 1 mês só). Antes,
    `obter()` tinha sua própria versão que chamava
    saldo_anterior_ao_vivo() por item do orçamento, recursiva, subindo a
    cadeia de meses anteriores no banco a cada passo — um orçamento com
    vários itens encadeados por vários meses virava dezenas de idas e
    voltas sequenciais numa página que carrega 1 mês só. Agora usa o
    mesmo helper de carregamento em lote que evolucao_orcamento() já
    usava: tem que ficar em 3 chamadas fixas, não crescer com o tamanho
    do histórico nem com o número de itens."""
    from app.auth import get_db
    from app.main import app

    from .fakes import FakeSupabaseClient

    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria_a = client.post("/categorias", json={"nome": "Aluguel"}).json()
    categoria_b = client.post("/categorias", json={"nome": "Mercado"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-01-01", "receita_base": 10000, "percentual_geral": 100}
    ).json()
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria_a["id"], "orcamento_mensal": 1000},
    )
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria_b["id"], "orcamento_mensal": 500},
    )
    # encadeia 6 meses via "gerar próximo mês" (jan-jun) — é isso que faz
    # a cadeia de saldo_anterior existir de verdade pros 2 itens
    for mes in range(1, 6):
        for categoria, valor in [(categoria_a, 700), (categoria_b, 300)]:
            client.post(
                "/transacoes",
                json={
                    "data_compra": f"2026-{mes:02d}-05",
                    "valor": valor,
                    "tipo_movimento": "despesa",
                    "conta_id": conta["id"],
                    "categoria_id": categoria["id"],
                    "estrutura_custo": "fixo" if categoria is categoria_a else "variavel",
                    "meio_pagamento": "pix",
                },
            )
        orcamento = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()

    class _ContadorClient:
        def __init__(self, store):
            self._inner = FakeSupabaseClient(store)
            self.chamadas: list[str] = []

        def table(self, nome):
            self.chamadas.append(nome)
            return self._inner.table(nome)

        def rpc(self, nome, params):
            self.chamadas.append(nome)
            return self._inner.rpc(nome, params)

    # pede só o ÚLTIMO mês da cadeia — é o pior caso pra recursão item a
    # item (precisa subir os 5 meses anteriores pra cada um dos 2 itens)
    contador = _ContadorClient(db_store)
    app.dependency_overrides[get_db] = lambda: contador
    try:
        resposta = client.get("/estrutura-custo/2026-06-01")
    finally:
        app.dependency_overrides[get_db] = lambda: FakeSupabaseClient(db_store)

    assert resposta.status_code == 200
    corpo = resposta.json()
    fixos = next(b for b in corpo["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos["itens"][0]["saldo_anterior"] != 0  # cadeia foi de fato calculada, não só "sem histórico"
    # 3 no total (orcamentos + orcamento_itens + transacoes), não crescendo
    # com o histórico (5 meses) nem com o número de itens (2) — sem o fix
    # seriam dezenas de chamadas (2 itens × ~5 meses de cadeia × 3 queries)
    assert contador.chamadas.count("orcamentos") == 1
    assert contador.chamadas.count("orcamento_itens") == 1
    assert contador.chamadas.count("saldo_transacoes_agregado") == 1
    assert len(contador.chamadas) == 3


def test_evolucao_orcamento_fim_antes_de_inicio_retorna_422(client):
    resposta = client.get(
        "/estrutura-custo/evolucao/tendencia", params={"inicio": "2026-09-01", "fim": "2026-07-01"}
    )
    assert resposta.status_code == 422
