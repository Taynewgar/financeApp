def test_resumo_mensal_contra_banco_real(real_client, headers_a, cleanup):
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
    corpo = resposta.json()
    assert corpo["receitas"] == 4000
    assert corpo["resultado_saude"] == 2500


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
