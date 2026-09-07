def _criar_orcamento(real_client, headers, vigencia_mes="2026-09-01"):
    # percentual_geral=100 dá teto folgado o bastante pra qualquer valor
    # usado nos testes que não estão testando o teto em si
    return real_client.post(
        "/orcamentos",
        json={"vigencia_mes": vigencia_mes, "receita_base": 5000, "percentual_geral": 100},
        headers=headers,
    ).json()


def test_criar_orcamento_e_recuperar_por_id(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))

    busca = real_client.get(f"/orcamentos/{orcamento['id']}", headers=headers_a)
    assert busca.status_code == 200
    assert busca.json()["vigencia_mes"] == "2026-09-01"


def test_orcamento_duplicado_no_mesmo_mes_e_bloqueado_pela_constraint_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a, vigencia_mes="2026-09-01")
    cleanup.append(("orcamentos", orcamento["id"]))

    repetido = real_client.post(
        "/orcamentos", json={"vigencia_mes": "2026-09-15"}, headers=headers_a
    )
    assert repetido.status_code == 409


def test_rls_impede_outro_usuario_de_ver_o_orcamento(real_client, headers_a, headers_b, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))

    busca_b = real_client.get(f"/orcamentos/{orcamento['id']}", headers=headers_b)
    assert busca_b.status_code == 404


def test_criar_item_vinculado_a_categoria_contra_banco_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))
    categoria = real_client.post("/categorias", json={"nome": "Moradia Integração"}, headers=headers_a).json()
    cleanup.append(("categorias", categoria["id"]))

    resposta = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1500},
        headers=headers_a,
    )
    assert resposta.status_code == 201
    item = resposta.json()
    cleanup.append(("orcamento_itens", item["id"]))
    assert item["orcamento_id"] == orcamento["id"]


def test_item_com_categoria_de_outro_usuario_retorna_404(real_client, headers_a, headers_b, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))
    categoria_de_b = real_client.post("/categorias", json={"nome": "Categoria de B"}, headers=headers_b).json()
    cleanup.append(("categorias", categoria_de_b["id"]))

    resposta = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria_de_b["id"]},
        headers=headers_a,
    )
    assert resposta.status_code == 404


def test_rls_impede_outro_usuario_de_ver_itens_do_orcamento(real_client, headers_a, headers_b, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))
    item = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel"},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))

    listagem_b = real_client.get(f"/orcamentos/{orcamento['id']}/itens", headers=headers_b)
    assert listagem_b.status_code == 404  # o próprio orçamento já não é visível para B


def test_proximo_mes_carrega_sobra_contra_banco_real(real_client, headers_a, cleanup):
    """Exige a migração de backend/tests/../../db/schema.sql (coluna
    orcamento_itens.saldo_anterior) já aplicada no seu projeto Supabase —
    veja o passo a passo no README antes de rodar esta suíte."""
    conta = real_client.post(
        "/contas", json={"nome": "Conta Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Restaurante Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    orcamento = _criar_orcamento(real_client, headers_a, vigencia_mes="2026-09-01")
    cleanup.append(("orcamentos", orcamento["id"]))
    item = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria["id"], "orcamento_mensal": 400},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))

    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 310,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    proximo = real_client.post(f"/orcamentos/{orcamento['id']}/proximo-mes", headers=headers_a)
    assert proximo.status_code == 201
    proximo_orcamento = proximo.json()
    cleanup.append(("orcamentos", proximo_orcamento["id"]))

    itens_proximo = real_client.get(f"/orcamentos/{proximo_orcamento['id']}/itens", headers=headers_a).json()
    cleanup.append(("orcamento_itens", itens_proximo[0]["id"]))
    assert itens_proximo[0]["saldo_anterior"] == 90
    assert itens_proximo[0]["disponivel"] == 490


def test_proximo_mes_chamado_duas_vezes_retorna_409_na_segunda_contra_banco_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a, vigencia_mes="2026-09-01")
    cleanup.append(("orcamentos", orcamento["id"]))

    primeira = real_client.post(f"/orcamentos/{orcamento['id']}/proximo-mes", headers=headers_a)
    assert primeira.status_code == 201
    cleanup.append(("orcamentos", primeira.json()["id"]))

    repetida = real_client.post(f"/orcamentos/{orcamento['id']}/proximo-mes", headers=headers_a)
    assert repetida.status_code == 409


def test_item_que_estoura_teto_do_bucket_retorna_422_contra_banco_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)  # receita_base=5000, teto_custos_fixos=2000
    cleanup.append(("orcamentos", orcamento["id"]))
    primeiro = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1800},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", primeiro["id"]))

    resposta = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Condomínio", "orcamento_mensal": 500},
        headers=headers_a,
    )
    assert resposta.status_code == 422  # 1800 + 500 = 2300 > teto de 2000


def test_item_expoe_percentuais_calculados_contra_banco_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)  # receita_base=5000
    cleanup.append(("orcamentos", orcamento["id"]))
    item = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1000},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))

    assert item["percentual_da_renda"] == 20.0  # 1000 / 5000 * 100
    assert item["percentual_do_teto"] == 50.0  # 1000 / 2000 * 100


def test_sobra_acumulada_do_bucket_amplia_teto_contra_banco_real(real_client, headers_a, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Sobra Integração", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))
    categoria = real_client.post(
        "/categorias", json={"nome": "Aluguel Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    setembro = _criar_orcamento(real_client, headers_a)  # receita_base=5000, teto_custos_fixos=2000
    cleanup.append(("orcamentos", setembro["id"]))
    item = real_client.post(
        f"/orcamentos/{setembro['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))
    transacao = real_client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 800,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
        headers=headers_a,
    ).json()
    cleanup.append(("transacoes", transacao["id"]))

    outubro = real_client.post(f"/orcamentos/{setembro['id']}/proximo-mes", headers=headers_a).json()
    cleanup.append(("orcamentos", outubro["id"]))
    itens_outubro = real_client.get(f"/orcamentos/{outubro['id']}/itens", headers=headers_a).json()
    cleanup.append(("orcamento_itens", itens_outubro[0]["id"]))

    # sem a sobra de 200, 1000 (aluguel) + 1000 = 2000 caberia exato; com a
    # sobra, o teto efetivo é 2200, então cabe mais um item de 1000 também
    resposta = real_client.post(
        f"/orcamentos/{outubro['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Novo item", "orcamento_mensal": 1200},
        headers=headers_a,
    )
    assert resposta.status_code == 201
    cleanup.append(("orcamento_itens", resposta.json()["id"]))

    estrutura = real_client.get("/estrutura-custo/2026-10-01", headers=headers_a).json()
    fixos = next(b for b in estrutura["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos["saldo_anterior_acumulado"] == 200


def test_desativar_item_persiste_no_banco_real(real_client, headers_a, cleanup):
    orcamento = _criar_orcamento(real_client, headers_a)
    cleanup.append(("orcamentos", orcamento["id"]))
    item = real_client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Reserva"},
        headers=headers_a,
    ).json()
    cleanup.append(("orcamento_itens", item["id"]))

    desativado = real_client.patch(
        f"/orcamentos/{orcamento['id']}/itens/{item['id']}/ativo", params={"ativo": False}, headers=headers_a
    )
    assert desativado.status_code == 200
    assert desativado.json()["ativo"] is False

    busca = real_client.get(f"/orcamentos/{orcamento['id']}/itens", headers=headers_a)
    item_buscado = next(i for i in busca.json() if i["id"] == item["id"])
    assert item_buscado["ativo"] is False
