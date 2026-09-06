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
        "sem_estrutura",
    }
    assert all(b["orcado"] == 0 and b["realizado"] == 0 and b["itens"] == [] for b in corpo["buckets"])


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
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert fixos["realizado"] == 1500
    assert fixos["orcado"] == 0
    assert fixos["itens"][0]["categoria_id"] == categoria["id"]


def test_despesa_sem_estrutura_custo_cai_em_sem_estrutura(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 80, "tipo_movimento": "despesa", "conta_id": conta["id"]},
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    assert _bucket(resposta, "sem_estrutura")["realizado"] == 80


def test_aplicacao_aparece_em_investimentos(client):
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 300, "tipo_movimento": "aplicacao", "conta_id": conta["id"]},
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    investimentos = _bucket(resposta, "investimentos")
    assert investimentos["realizado"] == 300
    assert investimentos["itens"][0]["conta_id"] == conta["id"]


def test_retirada_reduz_realizado_de_investimentos(client):
    conta = client.post("/contas", json={"nome": "Investimento", "tipo_conta": "investimento"}).json()
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 300, "tipo_movimento": "aplicacao", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-15", "valor": 100, "tipo_movimento": "retirada", "conta_id": conta["id"]},
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
    orcamento = client.post("/orcamentos", json={"vigencia_mes": "2026-09-01"}).json()
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
        },
    )

    resposta = client.get("/estrutura-custo/2026-09-01")
    fixos = _bucket(resposta, "custos_fixos")
    assert fixos["realizado"] == 1300
    valores_por_categoria = {i["categoria_id"]: i["realizado"] for i in fixos["itens"]}
    assert valores_por_categoria == {aluguel["id"]: 1200, internet["id"]: 100}


def test_transacao_fora_do_mes_nao_entra_no_calculo(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-31",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "estrutura_custo": "fixo",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-01",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "estrutura_custo": "fixo",
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
