from .conftest import OUTRO_USUARIO


def test_criar_subcategoria_vinculada_a_categoria_existente(client):
    categoria = client.post("/categorias", json={"nome": "Alimentação"}).json()

    resposta = client.post(
        "/subcategorias",
        json={"categoria_id": categoria["id"], "nome": "Mercado", "estrutura_custo_padrao": "variavel"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["categoria_id"] == categoria["id"]


def test_criar_subcategoria_com_categoria_inexistente_retorna_404(client):
    resposta = client.post(
        "/subcategorias",
        json={"categoria_id": "00000000-0000-0000-0000-000000000000", "nome": "Não deveria criar"},
    )
    assert resposta.status_code == 404


def test_criar_subcategoria_com_categoria_de_outro_usuario_retorna_404(client, current_user):
    categoria = client.post("/categorias", json={"nome": "Categoria do usuário A"}).json()

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(
        "/subcategorias",
        json={"categoria_id": categoria["id"], "nome": "Tentativa de vincular em categoria alheia"},
    )
    assert resposta.status_code == 404


def test_estrutura_custo_padrao_e_opcional(client):
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    resposta = client.post(
        "/subcategorias", json={"categoria_id": categoria["id"], "nome": "Viagens"}
    )
    assert resposta.status_code == 201
    assert resposta.json()["estrutura_custo_padrao"] is None


def test_estrutura_custo_invalida_retorna_422(client):
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    resposta = client.post(
        "/subcategorias",
        json={"categoria_id": categoria["id"], "nome": "Viagens", "estrutura_custo_padrao": "eventual"},
    )
    assert resposta.status_code == 422
