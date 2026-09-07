def test_filtro_por_categoria_e_periodo_contra_banco_real(real_client, headers_a, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Busca Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Mercado Busca Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    dentro = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 250,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
            "descricao": "Compra do mês",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", dentro["id"]))
    fora_do_periodo = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-01",
            "valor": 999,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", fora_do_periodo["id"]))

    resposta = real_client.get(
        "/transacoes",
        params={"categoria_id": categoria["id"], "data_inicio": "2026-09-01", "data_fim": "2026-09-30"},
        headers=headers_a,
    )
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["id"] == dentro["id"]


def test_resumo_contra_banco_real(real_client, headers_a, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Resumo Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    receita = real_client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 3000, "tipo_movimento": "receita", "conta_id": conta["id"]},
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", receita["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Resumo Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    despesa = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1000,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", despesa["id"]))

    # filtra por conta_id, não só por período — sem isso o teste conta
    # também outras transações reais do mesmo usuário no mesmo mês (ex: uso
    # manual do app durante testes), quebrando a igualdade exata
    resumo = real_client.get(
        "/transacoes/resumo",
        params={"conta_id": conta["id"], "data_inicio": "2026-09-01", "data_fim": "2026-09-30"},
        headers=headers_a,
    ).json()
    assert resumo["total_lancamentos"] == 2
    assert resumo["resultado_saude"] == 2000


def test_rls_nao_mistura_dados_de_outro_usuario(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta A Busca", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria RLS Busca Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta_b = real_client.get("/transacoes", headers=headers_b)
    assert not any(t["id"] == transacao["id"] for t in resposta_b.json())
