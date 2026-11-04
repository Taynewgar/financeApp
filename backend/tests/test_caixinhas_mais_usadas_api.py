from datetime import date, timedelta

from .conftest import OUTRO_USUARIO


def _criar_conta(client):
    return client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente", "saldo_inicial": 0}).json()


def _lancar_aporte(client, conta_id, caixinha_id, dias_atras=0, valor=10):
    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": (date.today() - timedelta(days=dias_atras)).isoformat(),
            "valor": valor,
            "tipo_movimento": "aplicacao",
            "conta_id": conta_id,
            "caixinha_id": caixinha_id,
        },
    )
    assert resposta.status_code == 201
    return resposta.json()


def test_caixinhas_mais_usadas_ordena_por_frequencia(client):
    conta = _criar_conta(client)
    viagem = client.post("/caixinhas", json={"nome": "Viagem"}).json()
    emergencia = client.post("/caixinhas", json={"nome": "Emergência"}).json()
    client.post("/caixinhas", json={"nome": "Nunca usada"})

    _lancar_aporte(client, conta["id"], viagem["id"], dias_atras=1, valor=10)
    _lancar_aporte(client, conta["id"], viagem["id"], dias_atras=2, valor=20)
    _lancar_aporte(client, conta["id"], viagem["id"], dias_atras=3, valor=30)
    _lancar_aporte(client, conta["id"], emergencia["id"], dias_atras=1, valor=40)

    resposta = client.get("/caixinhas/mais-usadas")
    assert resposta.status_code == 200
    nomes = [c["nome"] for c in resposta.json()]
    assert nomes[0] == "Viagem"
    assert nomes.index("Viagem") < nomes.index("Emergência")


def test_caixinhas_mais_usadas_conta_retirada_tambem(client):
    conta = _criar_conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Reforma"}).json()
    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": date.today().isoformat(),
            "valor": 50,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    assert resposta.status_code == 201

    nomes = [c["nome"] for c in client.get("/caixinhas/mais-usadas").json()]
    assert "Reforma" in nomes


def test_caixinhas_mais_usadas_ignora_uso_fora_da_janela(client):
    conta = _criar_conta(client)
    antiga = client.post("/caixinhas", json={"nome": "Só antiga"}).json()
    recente = client.post("/caixinhas", json={"nome": "Recente"}).json()

    _lancar_aporte(client, conta["id"], antiga["id"], dias_atras=200)  # fora da janela de 180 dias
    _lancar_aporte(client, conta["id"], recente["id"], dias_atras=5)

    nomes = [c["nome"] for c in client.get("/caixinhas/mais-usadas").json()]
    assert nomes[0] == "Recente"


def test_caixinhas_mais_usadas_respeita_limite(client):
    conta = _criar_conta(client)
    for i in range(8):
        caixinha = client.post("/caixinhas", json={"nome": f"Caixinha {i}"}).json()
        _lancar_aporte(client, conta["id"], caixinha["id"], dias_atras=i)

    resposta = client.get("/caixinhas/mais-usadas", params={"limite": 3})
    assert len(resposta.json()) == 3


def test_caixinhas_mais_usadas_nao_inclui_inativas(client):
    conta = _criar_conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Vai desativar"}).json()
    _lancar_aporte(client, conta["id"], caixinha["id"], dias_atras=1)
    client.patch(f"/caixinhas/{caixinha['id']}/ativo", params={"ativo": False})

    resposta = client.get("/caixinhas/mais-usadas")
    assert not any(c["id"] == caixinha["id"] for c in resposta.json())


def test_caixinhas_mais_usadas_nao_mistura_usuarios(client, current_user):
    conta = _criar_conta(client)
    caixinha = client.post("/caixinhas", json={"nome": "Da usuária A"}).json()
    _lancar_aporte(client, conta["id"], caixinha["id"], dias_atras=1)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.get("/caixinhas/mais-usadas")
    assert resposta.json() == []
