from .conftest import OUTRO_USUARIO


def _criar_conta_cartao(client, dia_fechamento=8):
    return client.post(
        "/contas",
        json={"nome": "Cartão", "tipo_conta": "cartao_credito", "dia_fechamento": dia_fechamento},
    ).json()


def _criar_conta_corrente(client):
    return client.post(
        "/contas", json={"nome": "Conta Corrente", "tipo_conta": "corrente", "saldo_inicial": 0}
    ).json()


def test_despesa_no_cartao_calcula_fatura_por_ciclo(client):
    cartao = _criar_conta_cartao(client, dia_fechamento=8)

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 89.90,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
        },
    )
    assert resposta.status_code == 201
    transacao = resposta.json()
    assert transacao["fatura_referencia"] == "2026-08-08"
    assert transacao["fatura_override"] is False


def test_receita_em_conta_corrente_nao_tem_fatura(client):
    conta = _criar_conta_corrente(client)

    resposta = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-01", "valor": 3000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    assert resposta.status_code == 201
    assert resposta.json()["fatura_referencia"] is None


def test_transacao_com_conta_de_outro_usuario_retorna_404(client, current_user):
    cartao = _criar_conta_cartao(client)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 10, "tipo_movimento": "despesa", "conta_id": cartao["id"]},
    )
    assert resposta.status_code == 404


def test_transacao_identica_repetida_retorna_409(client):
    cartao = _criar_conta_cartao(client)
    payload = {
        "data_compra": "2026-08-05",
        "valor": 50,
        "tipo_movimento": "despesa",
        "conta_id": cartao["id"],
        "descricao": "Mesma compra",
    }

    primeira = client.post("/transacoes", json=payload)
    assert primeira.status_code == 201

    repetida = client.post("/transacoes", json=payload)
    assert repetida.status_code == 409


def test_transacao_com_valor_diferente_nao_e_bloqueada_como_duplicada(client):
    cartao = _criar_conta_cartao(client)
    base = {
        "data_compra": "2026-08-05",
        "tipo_movimento": "despesa",
        "conta_id": cartao["id"],
        "descricao": "Compras diferentes",
    }

    primeira = client.post("/transacoes", json={**base, "valor": 50})
    segunda = client.post("/transacoes", json={**base, "valor": 51})
    assert primeira.status_code == 201
    assert segunda.status_code == 201


def test_estorno_vinculado_a_despesa_original(client):
    cartao = _criar_conta_cartao(client)
    despesa = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 100, "tipo_movimento": "despesa", "conta_id": cartao["id"]},
    ).json()

    estorno = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 20,
            "tipo_movimento": "estorno",
            "conta_id": cartao["id"],
            "ajuste_de_transacao_id": despesa["id"],
        },
    )
    assert estorno.status_code == 201
    assert estorno.json()["ajuste_de_transacao_id"] == despesa["id"]


def test_estorno_vinculado_a_transacao_de_outro_usuario_retorna_404(client, current_user):
    cartao = _criar_conta_cartao(client)
    despesa = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 100, "tipo_movimento": "despesa", "conta_id": cartao["id"]},
    ).json()

    current_user["id"] = OUTRO_USUARIO
    outro_cartao = _criar_conta_cartao(client)
    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 20,
            "tipo_movimento": "estorno",
            "conta_id": outro_cartao["id"],
            "ajuste_de_transacao_id": despesa["id"],
        },
    )
    assert resposta.status_code == 404


def test_mover_fatura_manualmente_marca_override(client):
    cartao = _criar_conta_cartao(client)
    transacao = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 30, "tipo_movimento": "despesa", "conta_id": cartao["id"]},
    ).json()
    assert transacao["fatura_referencia"] == "2026-08-08"

    movida = client.patch(f"/transacoes/{transacao['id']}/fatura", json={"fatura_referencia": "2026-09-08"})
    assert movida.status_code == 200
    assert movida.json()["fatura_referencia"] == "2026-09-08"
    assert movida.json()["fatura_override"] is True


def test_excluir_transacao(client):
    cartao = _criar_conta_cartao(client)
    transacao = client.post(
        "/transacoes",
        json={"data_compra": "2026-08-05", "valor": 30, "tipo_movimento": "despesa", "conta_id": cartao["id"]},
    ).json()

    excluida = client.delete(f"/transacoes/{transacao['id']}")
    assert excluida.status_code == 204

    busca = client.get(f"/transacoes/{transacao['id']}")
    assert busca.status_code == 404


def test_excluir_transacao_inexistente_retorna_404(client):
    resposta = client.delete("/transacoes/00000000-0000-0000-0000-000000000000")
    assert resposta.status_code == 404


def test_compra_parcelada_gera_uma_transacao_por_ciclo(client):
    cartao = _criar_conta_cartao(client)

    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 300.00,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
        },
    )
    assert resposta.status_code == 201
    parcelas = resposta.json()

    assert len(parcelas) == 3
    assert [p["data_compra"] for p in parcelas] == ["2026-08-05", "2026-09-05", "2026-10-05"]
    assert [p["parcela_atual"] for p in parcelas] == [1, 2, 3]
    assert all(p["parcela_total"] == 3 for p in parcelas)
    assert all(p["compra_parcelada_id"] == parcelas[0]["compra_parcelada_id"] for p in parcelas)
    # nenhuma perda por arredondamento: soma das parcelas == valor total
    assert round(sum(p["valor"] for p in parcelas), 2) == 300.00


def test_compra_parcelada_calcula_fatura_de_cada_parcela(client):
    cartao = _criar_conta_cartao(client, dia_fechamento=8)

    parcelas = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 30.00,
            "parcela_total": 2,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
        },
    ).json()

    assert parcelas[0]["fatura_referencia"] == "2026-08-08"
    assert parcelas[1]["fatura_referencia"] == "2026-09-08"


def test_compra_parcelada_com_conta_de_outro_usuario_retorna_404(client, current_user):
    cartao = _criar_conta_cartao(client)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 300,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
        },
    )
    assert resposta.status_code == 404
