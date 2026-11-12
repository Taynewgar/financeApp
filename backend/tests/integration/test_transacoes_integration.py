def _criar_cartao(real_client, headers, dia_fechamento=8):
    return real_client.post(
        "/contas",
        json={"nome": "Cartão Integração", "tipo_conta": "cartao_credito", "dia_fechamento": dia_fechamento},
        headers=headers,
    ).json()


def test_fatura_por_ciclo_contra_banco_real(real_client, headers_a, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 42.50,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    assert transacao["fatura_referencia"] == "2026-08-08"


def test_duplicata_e_bloqueada_pela_constraint_real(real_client, headers_a, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    payload = {
        "data_compra": "2026-08-05",
        "valor": 15.00,
        "tipo_movimento": "despesa",
        "conta_id": cartao["id"],
        "descricao": "Duplicata integração",
        "categoria_id": categoria["id"],
        "estrutura_custo": "variavel",
        "meio_pagamento": "cartao_credito",
    }
    primeira = real_client.post("/transacoes", json=payload, headers=headers_a)
    assert primeira.status_code == 201
    cleanup.append(("transacoes", primeira.json()["id"]))

    repetida = real_client.post("/transacoes", json=payload, headers=headers_a)
    assert repetida.status_code == 409


def test_rls_impede_outro_usuario_de_ver_a_transacao(real_client, headers_a, headers_b, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    busca_b = real_client.get(f"/transacoes/{transacao['id']}", headers=headers_b)
    assert busca_b.status_code == 404


def test_compra_parcelada_contra_banco_real(real_client, headers_a, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    resposta = real_client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook Integração",
            "valor_total": 300.00,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers_a,
    )
    assert resposta.status_code == 201
    parcelas = resposta.json()
    # apagar o grupo já apaga as parcelas em cascata (FK on delete cascade)
    cleanup.append(("compras_parceladas", parcelas[0]["compra_parcelada_id"]))

    assert len(parcelas) == 3
    assert round(sum(p["valor"] for p in parcelas), 2) == 300.00
    assert parcelas[0]["fatura_referencia"] == "2026-08-08"
    assert parcelas[1]["fatura_referencia"] == "2026-09-08"
    assert parcelas[2]["fatura_referencia"] == "2026-10-08"


def test_mover_fatura_manualmente_contra_banco_real(real_client, headers_a, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    movida = real_client.patch(
        f"/transacoes/{transacao['id']}/fatura", json={"fatura_referencia": "2026-09-08"}, headers=headers_a
    )
    assert movida.status_code == 200
    assert movida.json()["fatura_override"] is True


def test_mover_fatura_em_conta_que_nao_e_cartao_retorna_422_contra_banco_real(real_client, headers_a, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Corrente Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    resposta = real_client.patch(
        f"/transacoes/{transacao['id']}/fatura", json={"fatura_referencia": "2026-09-08"}, headers=headers_a
    )
    assert resposta.status_code == 422


def test_pix_parcelado_em_conta_corrente_contra_banco_real(real_client, headers_a, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Pix Parcelado Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    resposta = real_client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Pix Parcelado Integração",
            "valor_total": 300,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    )
    assert resposta.status_code == 201
    parcelas = resposta.json()
    cleanup.append(("compras_parceladas", parcelas[0]["compra_parcelada_id"]))
    assert all(p["fatura_referencia"] is None for p in parcelas)
    assert all(p["meio_pagamento"] == "pix" for p in parcelas)


def test_excluir_transacao_contra_banco_real(real_client, headers_a, cleanup):
    cartao = _criar_cartao(real_client, headers_a)
    cleanup.append(("contas", cartao["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers_a,
    ).json()

    excluida = real_client.delete(f"/transacoes/{transacao['id']}", headers=headers_a)
    assert excluida.status_code == 204

    busca = real_client.get(f"/transacoes/{transacao['id']}", headers=headers_a)
    assert busca.status_code == 404
