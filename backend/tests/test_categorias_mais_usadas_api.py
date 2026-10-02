from datetime import date, timedelta

from .conftest import OUTRO_USUARIO


def _criar_conta(client):
    return client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente", "saldo_inicial": 0}).json()


def _lancar_despesa(client, conta_id, categoria_id, subcategoria_id=None, dias_atras=0, valor=10):
    # hash_dedup (services/dedup.py) não considera categoria/subcategoria —
    # só data+valor+conta+tipo — por isso cada chamada com o mesmo
    # dias_atras precisa de um valor diferente pra não colidir em 409.
    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": (date.today() - timedelta(days=dias_atras)).isoformat(),
            "valor": valor,
            "tipo_movimento": "despesa",
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
            "descricao": f"despesa {dias_atras}/{valor}",
        },
    )
    assert resposta.status_code == 201
    return resposta.json()


def test_categorias_mais_usadas_ordena_por_frequencia(client):
    conta = _criar_conta(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post("/categorias", json={"nome": "Nunca usada"})

    _lancar_despesa(client, conta["id"], mercado["id"], dias_atras=1, valor=10)
    _lancar_despesa(client, conta["id"], mercado["id"], dias_atras=2, valor=20)
    _lancar_despesa(client, conta["id"], mercado["id"], dias_atras=3, valor=30)
    _lancar_despesa(client, conta["id"], lazer["id"], dias_atras=1, valor=40)

    resposta = client.get("/categorias/mais-usadas", params={"tipo": "despesa"})
    assert resposta.status_code == 200
    nomes = [c["nome"] for c in resposta.json()]
    assert nomes[0] == "Mercado"
    assert "Lazer" in nomes
    # "Nunca usada" some do topo, mas ainda aparece (empata por nome com contagem 0)
    assert nomes.index("Mercado") < nomes.index("Lazer")


def test_categorias_mais_usadas_ignora_uso_fora_da_janela(client):
    conta = _criar_conta(client)
    antiga = client.post("/categorias", json={"nome": "Só antiga"}).json()
    recente = client.post("/categorias", json={"nome": "Recente"}).json()

    _lancar_despesa(client, conta["id"], antiga["id"], dias_atras=200)  # fora da janela de 180 dias
    _lancar_despesa(client, conta["id"], recente["id"], dias_atras=5)

    resposta = client.get("/categorias/mais-usadas", params={"tipo": "despesa"})
    nomes = [c["nome"] for c in resposta.json()]
    assert nomes[0] == "Recente"


def test_categorias_mais_usadas_respeita_limite(client):
    conta = _criar_conta(client)
    for i in range(8):
        cat = client.post("/categorias", json={"nome": f"Categoria {i}"}).json()
        _lancar_despesa(client, conta["id"], cat["id"], dias_atras=i)

    resposta = client.get("/categorias/mais-usadas", params={"tipo": "despesa", "limite": 3})
    assert len(resposta.json()) == 3


def test_categorias_mais_usadas_nao_inclui_inativas(client):
    conta = _criar_conta(client)
    categoria = client.post("/categorias", json={"nome": "Vai desativar"}).json()
    _lancar_despesa(client, conta["id"], categoria["id"], dias_atras=1)
    client.patch(f"/categorias/{categoria['id']}/ativo", params={"ativo": False})

    resposta = client.get("/categorias/mais-usadas", params={"tipo": "despesa"})
    assert not any(c["id"] == categoria["id"] for c in resposta.json())


def test_categorias_mais_usadas_nao_mistura_usuarios(client, current_user):
    conta = _criar_conta(client)
    categoria = client.post("/categorias", json={"nome": "Da usuária A"}).json()
    _lancar_despesa(client, conta["id"], categoria["id"], dias_atras=1)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.get("/categorias/mais-usadas", params={"tipo": "despesa"})
    assert resposta.json() == []


def test_subcategorias_mais_usadas_ordena_e_filtra_por_categoria(client):
    conta = _criar_conta(client)
    categoria = client.post("/categorias", json={"nome": "Mercado"}).json()
    outra_categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    hortifruti = client.post(
        "/subcategorias", json={"categoria_id": categoria["id"], "nome": "Hortifruti"}
    ).json()
    acougue = client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Açougue"}).json()
    cinema = client.post(
        "/subcategorias", json={"categoria_id": outra_categoria["id"], "nome": "Cinema"}
    ).json()

    _lancar_despesa(client, conta["id"], categoria["id"], hortifruti["id"], dias_atras=1, valor=10)
    _lancar_despesa(client, conta["id"], categoria["id"], hortifruti["id"], dias_atras=2, valor=20)
    _lancar_despesa(client, conta["id"], categoria["id"], acougue["id"], dias_atras=1, valor=30)
    _lancar_despesa(client, conta["id"], outra_categoria["id"], cinema["id"], dias_atras=1, valor=40)

    resposta = client.get("/subcategorias/mais-usadas", params={"categoria_id": categoria["id"]})
    assert resposta.status_code == 200
    ids = [s["id"] for s in resposta.json()]
    assert ids[0] == hortifruti["id"]
    assert cinema["id"] not in ids


def test_subcategorias_mais_usadas_sem_filtro_considera_todas(client):
    conta = _criar_conta(client)
    categoria = client.post("/categorias", json={"nome": "Mercado"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Hortifruti"}).json()
    _lancar_despesa(client, conta["id"], categoria["id"], sub["id"], dias_atras=1)

    resposta = client.get("/subcategorias/mais-usadas")
    assert resposta.status_code == 200
    assert any(s["id"] == sub["id"] for s in resposta.json())
