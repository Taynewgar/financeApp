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

    _despesa(client, conta["id"], 5800, "fixo")
    _despesa(client, conta["id"], 2500, "variavel")
    _despesa(client, conta["id"], 1000, "sazonal")

    resposta = client.get("/estrutura-custo/2026-09-01").json()
    assert _bucket(client.get("/estrutura-custo/2026-09-01"), "custos_fixos")["realizado"] == 5800  # estourou sozinho
    assert resposta["pool_despesas"]["teto"] == 10125
    assert resposta["pool_despesas"]["realizado"] == 9300
    assert resposta["pool_despesas"]["dentro_do_teto"] is True


def test_pool_despesas_estoura_quando_soma_total_passa_do_teto_agregado(client):
    _criar_orcamento_do_exemplo(client)
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()

    _despesa(client, conta["id"], 6000, "fixo")
    _despesa(client, conta["id"], 3000, "variavel")
    _despesa(client, conta["id"], 1500, "sazonal")

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
