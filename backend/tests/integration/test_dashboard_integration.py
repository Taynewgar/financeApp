def test_resumo_mensal_contra_banco_real(real_client, headers_a, cleanup):
    # /dashboard/mensal agrega o mês inteiro do usuário sem filtro por
    # conta (é o resumo financeiro completo, por design) — por isso mede a
    # DIFERENÇA antes/depois de criar as transações do teste, em vez de
    # assumir que não há mais nada lançado nesse mês (o usuário pode ter
    # uso manual real do app misturado no mesmo período).
    antes = real_client.get("/dashboard/mensal/2026-09-01", headers=headers_a).json()

    conta = real_client.post(
        "/contas", json={"nome": "Conta Dashboard Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    receita = real_client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 4000, "tipo_movimento": "receita", "conta_id": conta["id"]},
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", receita["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Dashboard Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    despesa = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", despesa["id"]))

    resposta = real_client.get("/dashboard/mensal/2026-09-01", headers=headers_a)
    assert resposta.status_code == 200
    depois = resposta.json()
    assert round(depois["receitas"] - antes["receitas"], 2) == 4000
    # arredonda antes de comparar — soma de floats de centavos (ex: dados de
    # seed com valores aleatórios) pode deixar a subtração tipo 2500.0000000000005
    assert round(depois["resultado_saude"] - antes["resultado_saude"], 2) == 2500


def test_rls_nao_mistura_dados_de_outro_usuario(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta A Dashboard", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    receita = real_client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 9999, "tipo_movimento": "receita", "conta_id": conta["id"]},
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", receita["id"]))

    resposta_b = real_client.get("/dashboard/mensal/2026-09-01", headers=headers_b)
    assert resposta_b.status_code == 200
    assert resposta_b.json()["receitas"] == 0
