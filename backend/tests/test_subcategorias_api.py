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


def test_criar_subcategoria_com_nome_duplicado_na_mesma_categoria_retorna_409(client):
    categoria = client.post("/categorias", json={"nome": "Mercado"}).json()
    client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Feira"})

    repetida = client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Feira"})
    assert repetida.status_code == 409


def test_mesmo_nome_de_subcategoria_em_categorias_diferentes_e_aceito(client):
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post("/subcategorias", json={"categoria_id": mercado["id"], "nome": "Assinaturas"})

    em_outra_categoria = client.post("/subcategorias", json={"categoria_id": lazer["id"], "nome": "Assinaturas"})
    assert em_outra_categoria.status_code == 201  # unique é por (categoria_id, nome), não global


def test_estrutura_custo_padrao_aceita_investimentos(client):
    investimentos = client.post("/categorias", json={"nome": "Investimentos", "tipo": "investimento"}).json()
    resposta = client.post(
        "/subcategorias",
        json={
            "categoria_id": investimentos["id"],
            "nome": "Reserva de Emergência",
            "estrutura_custo_padrao": "investimentos",
        },
    )
    assert resposta.status_code == 201
    assert resposta.json()["estrutura_custo_padrao"] == "investimentos"
