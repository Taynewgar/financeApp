from .conftest import OUTRO_USUARIO


def test_criar_caixinha_vinculada_a_conta_existente(client):
    conta = client.post(
        "/contas", json={"nome": "Reserva", "tipo_conta": "caixinha"}
    ).json()

    resposta = client.post("/caixinhas", json={"nome": "Emergência", "conta_id": conta["id"]})
    assert resposta.status_code == 201
    assert resposta.json()["conta_id"] == conta["id"]


def test_criar_caixinha_sem_conta_e_valido(client):
    resposta = client.post("/caixinhas", json={"nome": "Viagem"})
    assert resposta.status_code == 201
    assert resposta.json()["conta_id"] is None


def test_criar_caixinha_com_nome_duplicado_retorna_409(client):
    client.post("/caixinhas", json={"nome": "Viagem"})

    repetida = client.post("/caixinhas", json={"nome": "Viagem"})
    assert repetida.status_code == 409


def test_criar_caixinha_com_conta_inexistente_retorna_404(client):
    resposta = client.post(
        "/caixinhas", json={"nome": "X", "conta_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert resposta.status_code == 404


def test_criar_caixinha_com_conta_de_outro_usuario_retorna_404(client, current_user):
    conta = client.post("/contas", json={"nome": "Reserva", "tipo_conta": "caixinha"}).json()

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post("/caixinhas", json={"nome": "X", "conta_id": conta["id"]})
    assert resposta.status_code == 404


def test_trocar_conta_vinculada_da_caixinha_e_aceito(client):
    conta_a = client.post("/contas", json={"nome": "Conta A", "tipo_conta": "caixinha"}).json()
    conta_b = client.post("/contas", json={"nome": "Conta B", "tipo_conta": "caixinha"}).json()
    caixinha = client.post("/caixinhas", json={"nome": "Emergência", "conta_id": conta_a["id"]}).json()

    resposta = client.patch(f"/caixinhas/{caixinha['id']}", json={"conta_id": conta_b["id"]})
    assert resposta.status_code == 200
    assert resposta.json()["conta_id"] == conta_b["id"]


def test_vincular_conta_em_caixinha_sem_conta_e_aceito(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "caixinha"}).json()
    caixinha = client.post("/caixinhas", json={"nome": "Viagem"}).json()

    resposta = client.patch(f"/caixinhas/{caixinha['id']}", json={"conta_id": conta["id"]})
    assert resposta.status_code == 200
    assert resposta.json()["conta_id"] == conta["id"]
