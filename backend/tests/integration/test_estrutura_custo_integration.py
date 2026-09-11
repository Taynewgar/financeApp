def _bucket(resposta, nome):
    return next(b for b in resposta.json()["buckets"] if b["bucket"] == nome)


def test_orcado_e_realizado_contra_banco_real(real_client, headers_a, cleanup):
    # "realizado" do bucket soma TODAS as despesas variavel do mês do
    # usuário, não só desta categoria (mesmo motivo do pool_despesas/
    # piso_investimentos) — mede a diferença antes/depois em vez do total
    # absoluto, pra não quebrar com outras despesas reais no mesmo bucket/mês.
    antes = next(b for b in real_client.get("/estrutura-custo/2026-09-01", headers=headers_a).json()["buckets"] if b["bucket"] == "custos_variaveis")
    orcado_variaveis_antes = antes["orcado"]
    realizado_variaveis_antes = antes["realizado"]

    conta = real_client.post(
        "/contas", json={"nome": "Conta Estrutura Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Mercado Estrutura Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    orcamento = real_client.post(
        "/orcamentos",
        json={"vigencia_mes": "2026-09-01", "receita_base": 5000, "percentual_geral": 100},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamentos", orcamento["id"]))
    item = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria["id"], "orcamento_mensal": 500},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))

    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 320,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta = real_client.get("/estrutura-custo/2026-09-01", headers=headers_a)
    assert resposta.status_code == 200
    variaveis = _bucket(resposta, "custos_variaveis")
    # arredonda antes de comparar — soma de floats de centavos (ex: dados de
    # seed com valores aleatórios) pode deixar a subtração fora do exato
    assert round(variaveis["orcado"] - orcado_variaveis_antes, 2) == 500
    assert round(variaveis["realizado"] - realizado_variaveis_antes, 2) == 320


def test_pool_despesas_e_piso_investimentos_contra_banco_real(real_client, headers_a, cleanup):
    # receita_base=15000, percentual_geral=90% → teto_fixos=5400,
    # teto_variaveis=3375, teto_sazonalidades=1350 (pool=10125), teto_investimentos=3375
    orcamento = real_client.post(
        "/orcamentos",
        json={"vigencia_mes": "2026-09-01", "receita_base": 15000, "percentual_geral": 90},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamentos", orcamento["id"]))

    # pool_despesas/piso_investimentos somam o mês inteiro do usuário, sem
    # filtro por conta (mesmo motivo do /dashboard/mensal) — mede a
    # diferença antes/depois em vez do total absoluto, pra não quebrar
    # com outras transações reais do usuário no mesmo mês.
    antes = real_client.get("/estrutura-custo/2026-09-01", headers=headers_a).json()
    realizado_pool_antes = antes["pool_despesas"]["realizado"]
    realizado_investimentos_antes = antes["piso_investimentos"]["realizado"]

    conta = real_client.post(
        "/contas", json={"nome": "Conta Pool Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Pool Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    for valor, estrutura in ((5800, "fixo"), (2500, "variavel"), (1000, "sazonal")):
        t = real_client.post(
            "/transacoes",
            json={
                "data_compra": "2026-09-05",
                "valor": valor,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "categoria_id": categoria["id"],
                "estrutura_custo": estrutura,
                "meio_pagamento": "pix",
            },
            headers=headers_a,
        ).json()
        cleanup.append(("transacoes", t["id"]))

    conta_investimento = real_client.post(
        "/contas", json={"nome": "Investimento Integração", "tipo_conta": "investimento"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta_investimento["id"]))
    aplicacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 4000,
            "tipo_movimento": "aplicacao",
            "conta_id": conta_investimento["id"],
            "estrutura_custo": "investimentos",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", aplicacao["id"]))

    resposta = real_client.get("/estrutura-custo/2026-09-01", headers=headers_a).json()
    # arredonda antes de comparar — soma de floats de centavos (ex: dados de
    # seed com valores aleatórios) pode deixar a subtração com resto tipo
    # 9300.000000000002 em vez de 9300.0 exato
    assert resposta["pool_despesas"]["teto"] == 10125.0
    assert round(resposta["pool_despesas"]["realizado"] - realizado_pool_antes, 2) == 9300.0
    assert resposta["piso_investimentos"]["teto"] == 3375.0
    assert round(resposta["piso_investimentos"]["realizado"] - realizado_investimentos_antes, 2) == 4000.0


def test_rls_nao_mistura_dados_de_outro_usuario(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta A", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria RLS Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta_b = real_client.get("/estrutura-custo/2026-09-01", headers=headers_b)
    assert resposta_b.status_code == 200
    assert _bucket(resposta_b, "custos_fixos")["realizado"] == 0
