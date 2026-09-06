def _criar_orcamento(real_client, headers, vigencia_mes="2026-09-01"):
    return real_client.post(
        "/orcamentos",
        json={"vigencia_mes": vigencia_mes, "receita_base": 5000},
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
