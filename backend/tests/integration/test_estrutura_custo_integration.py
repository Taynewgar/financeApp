def _bucket(resposta, nome):
    return next(b for b in resposta.json()["buckets"] if b["bucket"] == nome)


def test_orcado_e_realizado_contra_banco_real(real_client, headers_a, cleanup):
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
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta = real_client.get("/estrutura-custo/2026-09-01", headers=headers_a)
    assert resposta.status_code == 200
    variaveis = _bucket(resposta, "custos_variaveis")
    assert variaveis["orcado"] == 500
    assert variaveis["realizado"] == 320


def test_pool_despesas_e_piso_investimentos_contra_banco_real(real_client, headers_a, cleanup):
    # receita_base=15000, percentual_geral=90% → teto_fixos=5400,
    # teto_variaveis=3375, teto_sazonalidades=1350 (pool=10125), teto_investimentos=3375
    orcamento = real_client.post(
        "/orcamentos",
        json={"vigencia_mes": "2026-09-01", "receita_base": 15000, "percentual_geral": 90},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamentos", orcamento["id"]))

    conta = real_client.post(
        "/contas", json={"nome": "Conta Pool Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    for valor, estrutura in ((5800, "fixo"), (2500, "variavel"), (1000, "sazonal")):
        t = real_client.post(
            "/transacoes",
            json={
                "data_compra": "2026-09-05",
                "valor": valor,
                "tipo_movimento": "despesa",
                "conta_id": conta["id"],
                "estrutura_custo": estrutura,
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
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", aplicacao["id"]))

    resposta = real_client.get("/estrutura-custo/2026-09-01", headers=headers_a).json()
    assert resposta["pool_despesas"] == {"teto": 10125.0, "realizado": 9300.0, "dentro_do_teto": True}
    assert resposta["piso_investimentos"] == {"teto": 3375.0, "realizado": 4000.0, "meta_batida": True}


def test_rls_nao_mistura_dados_de_outro_usuario(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta A", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "estrutura_custo": "fixo",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta_b = real_client.get("/estrutura-custo/2026-09-01", headers=headers_b)
    assert resposta_b.status_code == 200
    assert _bucket(resposta_b, "custos_fixos")["realizado"] == 0
