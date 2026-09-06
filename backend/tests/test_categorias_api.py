from .conftest import OUTRO_USUARIO


def test_criar_categoria_e_listar(client):
    resposta = client.post("/categorias", json={"nome": "Alimentação"})
    assert resposta.status_code == 201
    categoria = resposta.json()
    assert categoria["nome"] == "Alimentação"
    assert categoria["ativo"] is True

    listagem = client.get("/categorias")
    assert listagem.status_code == 200
    assert any(c["id"] == categoria["id"] for c in listagem.json())


def test_criar_categoria_sem_campo_obrigatorio_retorna_422(client):
    resposta = client.post("/categorias", json={})
    assert resposta.status_code == 422


def test_desativar_categoria_nao_exclui(client):
    categoria = client.post("/categorias", json={"nome": "Transporte"}).json()

    desativada = client.patch(f"/categorias/{categoria['id']}/ativo", params={"ativo": False})
    assert desativada.status_code == 200
    assert desativada.json()["ativo"] is False

    # continua existindo e aparecendo na listagem — só marcada como inativa
    busca = client.get(f"/categorias/{categoria['id']}")
    assert busca.status_code == 200
    assert busca.json()["ativo"] is False

    listagem = client.get("/categorias")
    assert any(c["id"] == categoria["id"] for c in listagem.json())


def test_reativar_categoria(client):
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.patch(f"/categorias/{categoria['id']}/ativo", params={"ativo": False})

    reativada = client.patch(f"/categorias/{categoria['id']}/ativo", params={"ativo": True})
    assert reativada.status_code == 200
    assert reativada.json()["ativo"] is True


def test_editar_categoria_inexistente_retorna_404(client):
    resposta = client.patch(
        "/categorias/00000000-0000-0000-0000-000000000000",
        json={"nome": "Não existe"},
    )
    assert resposta.status_code == 404


def test_usuario_nao_ve_categoria_de_outro_usuario(client, current_user):
    categoria = client.post("/categorias", json={"nome": "Só do usuário A"}).json()

    current_user["id"] = OUTRO_USUARIO
    listagem = client.get("/categorias")
    assert not any(c["id"] == categoria["id"] for c in listagem.json())

    busca = client.get(f"/categorias/{categoria['id']}")
    assert busca.status_code == 404
