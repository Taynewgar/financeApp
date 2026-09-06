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
        "/orcamentos", json={"vigencia_mes": "2026-09-01"}, headers=headers_a
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
