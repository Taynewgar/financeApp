from .conftest import OUTRO_USUARIO


def _criar_orcamento(client, vigencia_mes="2026-09-01", **extra):
    return client.post("/orcamentos", json={"vigencia_mes": vigencia_mes, **extra}).json()


def test_criar_orcamento_e_listar(client):
    resposta = client.post(
        "/orcamentos",
        json={"vigencia_mes": "2026-09-01", "receita_base": 5000, "percentual_geral": 100},
    )
    assert resposta.status_code == 201
    orcamento = resposta.json()
    assert orcamento["receita_base"] == 5000
    assert orcamento["limite_custos_fixos"] == 40  # default do schema

    listagem = client.get("/orcamentos")
    assert listagem.status_code == 200
    assert any(o["id"] == orcamento["id"] for o in listagem.json())


def test_criar_orcamento_normaliza_vigencia_para_primeiro_dia_do_mes(client):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-15")
    assert orcamento["vigencia_mes"] == "2026-09-01"


def test_criar_orcamento_sem_campo_obrigatorio_retorna_422(client):
    resposta = client.post("/orcamentos", json={})
    assert resposta.status_code == 422


def test_criar_orcamento_duplicado_no_mesmo_mes_retorna_409(client):
    _criar_orcamento(client, vigencia_mes="2026-09-01")

    repetido = client.post("/orcamentos", json={"vigencia_mes": "2026-09-20"})
    assert repetido.status_code == 409


def test_orcamentos_de_meses_diferentes_nao_conflitam(client):
    primeiro = client.post("/orcamentos", json={"vigencia_mes": "2026-09-01"})
    segundo = client.post("/orcamentos", json={"vigencia_mes": "2026-10-01"})
    assert primeiro.status_code == 201
    assert segundo.status_code == 201


def test_atualizar_orcamento(client):
    orcamento = _criar_orcamento(client)

    atualizado = client.patch(f"/orcamentos/{orcamento['id']}", json={"receita_base": 6000})
    assert atualizado.status_code == 200
    assert atualizado.json()["receita_base"] == 6000


def test_editar_orcamento_inexistente_retorna_404(client):
    resposta = client.patch(
        "/orcamentos/00000000-0000-0000-0000-000000000000",
        json={"receita_base": 1000},
    )
    assert resposta.status_code == 404


def test_usuario_nao_ve_orcamento_de_outro_usuario(client, current_user):
    orcamento = _criar_orcamento(client)

    current_user["id"] = OUTRO_USUARIO
    listagem = client.get("/orcamentos")
    assert not any(o["id"] == orcamento["id"] for o in listagem.json())

    busca = client.get(f"/orcamentos/{orcamento['id']}")
    assert busca.status_code == 404


def test_criar_item_vinculado_a_categoria_existente(client):
    orcamento = _criar_orcamento(client)
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1500},
    )
    assert resposta.status_code == 201
    item = resposta.json()
    assert item["orcamento_id"] == orcamento["id"]
    assert item["categoria_id"] == categoria["id"]
    assert item["ativo"] is True


def test_criar_item_sem_categoria_com_nome_livre_e_valido(client):
    orcamento = _criar_orcamento(client)

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Liberdade Financeira", "orcamento_mensal": 800},
    )
    assert resposta.status_code == 201
    assert resposta.json()["categoria_id"] is None


def test_criar_item_com_categoria_inexistente_retorna_404(client):
    orcamento = _criar_orcamento(client)

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resposta.status_code == 404


def test_criar_item_com_categoria_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()

    current_user["id"] = OUTRO_USUARIO
    outro_orcamento = _criar_orcamento(client)
    resposta = client.post(
        f"/orcamentos/{outro_orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"]},
    )
    assert resposta.status_code == 404


def test_criar_item_com_conta_vinculada_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)
    conta = client.post("/contas", json={"nome": "Reserva", "tipo_conta": "investimento"}).json()

    current_user["id"] = OUTRO_USUARIO
    outro_orcamento = _criar_orcamento(client)
    resposta = client.post(
        f"/orcamentos/{outro_orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Reserva", "conta_vinculada_id": conta["id"]},
    )
    assert resposta.status_code == 404


def test_criar_item_em_orcamento_inexistente_retorna_404(client):
    resposta = client.post(
        "/orcamentos/00000000-0000-0000-0000-000000000000/itens",
        json={"bucket": "custos_fixos", "nome": "X"},
    )
    assert resposta.status_code == 404


def test_criar_item_em_orcamento_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Invasão"},
    )
    assert resposta.status_code == 404


def test_listar_itens_de_um_orcamento(client):
    orcamento = _criar_orcamento(client)
    client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"})
    client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "investimentos", "nome": "Reserva"})

    outro_orcamento = _criar_orcamento(client, vigencia_mes="2026-10-01")
    client.post(f"/orcamentos/{outro_orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Outro mês"})

    listagem = client.get(f"/orcamentos/{orcamento['id']}/itens")
    assert listagem.status_code == 200
    nomes = {item["nome"] for item in listagem.json()}
    assert nomes == {"Aluguel", "Reserva"}


def test_atualizar_item(client):
    orcamento = _criar_orcamento(client)
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1000}
    ).json()

    atualizado = client.patch(
        f"/orcamentos/{orcamento['id']}/itens/{item['id']}", json={"orcamento_mensal": 1200}
    )
    assert atualizado.status_code == 200
    assert atualizado.json()["orcamento_mensal"] == 1200


def test_atualizar_item_inexistente_retorna_404(client):
    orcamento = _criar_orcamento(client)

    resposta = client.patch(
        f"/orcamentos/{orcamento['id']}/itens/00000000-0000-0000-0000-000000000000",
        json={"orcamento_mensal": 100},
    )
    assert resposta.status_code == 404


def test_desativar_item_nao_exclui(client):
    orcamento = _criar_orcamento(client)
    item = client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"}).json()

    desativado = client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}/ativo", params={"ativo": False})
    assert desativado.status_code == 200
    assert desativado.json()["ativo"] is False

    listagem = client.get(f"/orcamentos/{orcamento['id']}/itens")
    assert any(i["id"] == item["id"] for i in listagem.json())


def test_usuario_nao_atualiza_item_de_orcamento_de_outro_usuario(client, current_user):
    orcamento = _criar_orcamento(client)
    item = client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"}).json()

    current_user["id"] = OUTRO_USUARIO
    resposta = client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}", json={"orcamento_mensal": 1})
    assert resposta.status_code == 404
