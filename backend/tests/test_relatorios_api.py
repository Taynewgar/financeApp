def _criar_conta_corrente(client):
    return client.post(
        "/contas", json={"nome": "Conta Corrente", "tipo_conta": "corrente", "saldo_inicial": 0}
    ).json()


def test_relatorio_mensal_estrutura_basica(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 100,
            "descricao": "Cinema",
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/relatorios/mes/2026-09-01")
    assert resposta.status_code == 200
    corpo = resposta.json()

    assert corpo["periodo"] == {"tipo": "mes", "inicio": "2026-09-01", "fim": "2026-09-30"}
    assert corpo["resumo"]["despesas_brutas"] == 100
    assert len(corpo["lancamentos"]) == 1
    assert corpo["lancamentos"][0]["descricao"] == "Cinema"
    assert corpo["lancamentos"][0]["categoria_nome"] == "Lazer"
    assert corpo["lancamentos"][0]["conta_nome"] == "Conta Corrente"
    assert any(d["categoria_nome"] == "Lazer" and d["valor"] == 100 for d in corpo["despesas_por_categoria"])
    assert corpo["estrutura_custo"]["vigencia_mes"] == "2026-09-01"
    assert corpo["caixinhas_patrimonio"] == []
    assert corpo["retiradas_pendentes"] == []


def test_relatorio_mensal_resolve_nome_da_caixinha_origem(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    caixinha = client.post("/caixinhas", json={"nome": "Viagem"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
            "caixinha_origem_id": caixinha["id"],
        },
    )

    corpo = client.get("/relatorios/mes/2026-09-01").json()
    assert corpo["lancamentos"][0]["caixinha_origem_nome"] == "Viagem"
    assert len(corpo["retiradas_pendentes"]) == 1


def test_relatorio_mensal_mes_sem_lancamentos_fica_vazio(client):
    corpo = client.get("/relatorios/mes/2026-01-01").json()
    assert corpo["lancamentos"] == []
    assert corpo["resumo"]["despesas_brutas"] == 0
    assert corpo["estrutura_custo"]["orcamento_id"] is None


def test_relatorio_anual_estrutura_basica(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-03-10",
            "valor": 200,
            "descricao": "Viagem",
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "sazonal",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/relatorios/ano/2026")
    assert resposta.status_code == 200
    corpo = resposta.json()

    assert corpo["periodo"] == {"tipo": "ano", "inicio": "2026-01-01", "fim": "2026-12-31"}
    assert len(corpo["evolucao_mensal"]) == 12
    assert len(corpo["estrutura_custo_mensal"]) == 12
    assert corpo["resumo"]["despesas_brutas"] == 200
    assert len(corpo["lancamentos"]) == 1
    assert corpo["lancamentos"][0]["descricao"] == "Viagem"
    marco = next(m for m in corpo["evolucao_mensal"] if m["vigencia_mes"] == "2026-03-01")
    assert marco["despesas_brutas"] == 200
