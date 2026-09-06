def test_criar_conta_e_recuperar_por_id(real_client, headers_a, cleanup):
    resposta = real_client.post(
        "/contas",
        json={"nome": "Conta Integração", "tipo_conta": "corrente", "saldo_inicial": 10},
        headers=headers_a,
    )
    assert resposta.status_code == 201
    conta = resposta.json()
    cleanup.append(("contas", conta["id"]))

    busca = real_client.get(f"/contas/{conta['id']}", headers=headers_a)
    assert busca.status_code == 200
    assert busca.json()["id"] == conta["id"]


def test_rls_impede_outro_usuario_de_ver_a_conta(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Privada", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))

    listagem_b = real_client.get("/contas", headers=headers_b)
    assert listagem_b.status_code == 200
    assert not any(c["id"] == conta["id"] for c in listagem_b.json())


def test_rls_impede_outro_usuario_de_editar_a_conta(real_client, headers_a, headers_b, cleanup):
    conta = real_client.post(
        "/contas", json={"nome": "Conta Privada 2", "tipo_conta": "corrente"}, headers=headers_a
    ).json()
    cleanup.append(("contas", conta["id"]))

    tentativa = real_client.patch(f"/contas/{conta['id']}", json={"nome": "Invasão"}, headers=headers_b)
    assert tentativa.status_code == 404  # aplicado pelo RLS do Postgres, não só pelo código da API

    ainda_intacta = real_client.get(f"/contas/{conta['id']}", headers=headers_a)
    assert ainda_intacta.json()["nome"] == "Conta Privada 2"


def test_categoria_desativada_persiste_no_banco_real(real_client, headers_a, cleanup):
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria Integração"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    desativada = real_client.patch(
        f"/categorias/{categoria['id']}/ativo", params={"ativo": False}, headers=headers_a
    )
    assert desativada.status_code == 200
    assert desativada.json()["ativo"] is False

    busca = real_client.get(f"/categorias/{categoria['id']}", headers=headers_a)
    assert busca.json()["ativo"] is False


def test_subcategoria_com_categoria_de_outro_usuario_retorna_404(real_client, headers_a, headers_b, cleanup):
    categoria = real_client.post(
        "/categorias", json={"nome": "Categoria do usuário A"}, headers=headers_a
    ).json()
    cleanup.append(("categorias", categoria["id"]))

    tentativa = real_client.post(
        "/subcategorias",
        json={"categoria_id": categoria["id"], "nome": "Tentativa de vincular em categoria alheia"},
        headers=headers_b,
    )
    assert tentativa.status_code == 404
