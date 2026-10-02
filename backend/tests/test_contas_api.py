def test_criar_conta_corrente_e_buscar_por_id(client):
    criada = client.post(
        "/contas", json={"nome": "Conta Corrente", "tipo_conta": "corrente", "saldo_inicial": 500}
    )
    assert criada.status_code == 201
    conta = criada.json()
    assert conta["saldo_inicial"] == 500
    assert conta["dia_fechamento"] is None

    busca = client.get(f"/contas/{conta['id']}")
    assert busca.status_code == 200
    assert busca.json()["id"] == conta["id"]


def test_criar_conta_cartao_com_dia_fechamento(client):
    resposta = client.post(
        "/contas", json={"nome": "Cartão", "tipo_conta": "cartao_credito", "dia_fechamento": 8}
    )
    assert resposta.status_code == 201
    assert resposta.json()["dia_fechamento"] == 8


def test_tipo_conta_invalido_retorna_422(client):
    resposta = client.post("/contas", json={"nome": "X", "tipo_conta": "poupanca-inventada"})
    assert resposta.status_code == 422


def test_dia_fechamento_fora_do_intervalo_retorna_422(client):
    resposta = client.post(
        "/contas", json={"nome": "Cartão", "tipo_conta": "cartao_credito", "dia_fechamento": 32}
    )
    assert resposta.status_code == 422


def test_editar_dia_fechamento_de_conta_existente(client):
    conta = client.post(
        "/contas", json={"nome": "Cartão", "tipo_conta": "cartao_credito", "dia_fechamento": 8}
    ).json()

    editada = client.patch(f"/contas/{conta['id']}", json={"dia_fechamento": 15})
    assert editada.status_code == 200
    assert editada.json()["dia_fechamento"] == 15


def test_buscar_conta_inexistente_retorna_404(client):
    resposta = client.get("/contas/00000000-0000-0000-0000-000000000000")
    assert resposta.status_code == 404
