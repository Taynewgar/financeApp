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
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 89.90,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
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
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    payload = {
        "data_compra": "2026-08-05",
        "valor": 50,
        "tipo_movimento": "despesa",
        "conta_id": cartao["id"],
        "descricao": "Mesma compra",
        "categoria_id": categoria["id"],
        "estrutura_custo": "variavel",
        "meio_pagamento": "cartao_credito",
    }

    primeira = client.post("/transacoes", json=payload)
    assert primeira.status_code == 201

    repetida = client.post("/transacoes", json=payload)
    assert repetida.status_code == 409


def test_transacao_com_valor_diferente_nao_e_bloqueada_como_duplicada(client):
    cartao = _criar_conta_cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    base = {
        "data_compra": "2026-08-05",
        "tipo_movimento": "despesa",
        "conta_id": cartao["id"],
        "descricao": "Compras diferentes",
        "categoria_id": categoria["id"],
        "estrutura_custo": "variavel",
        "meio_pagamento": "cartao_credito",
    }

    primeira = client.post("/transacoes", json={**base, "valor": 50})
    segunda = client.post("/transacoes", json={**base, "valor": 51})
    assert primeira.status_code == 201
    assert segunda.status_code == 201


def test_estorno_vinculado_a_despesa_original(client):
    cartao = _criar_conta_cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    despesa = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
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
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    despesa = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
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


def test_mover_fatura_em_conta_que_nao_e_cartao_retorna_422(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    transacao = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    ).json()

    resposta = client.patch(
        f"/transacoes/{transacao['id']}/fatura", json={"fatura_referencia": "2026-10-01"}
    )
    assert resposta.status_code == 422


def test_meio_pagamento_e_gravado_e_pode_ser_filtrado(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 40,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 60,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "boleto",
        },
    )

    resposta = client.get("/transacoes", params={"meio_pagamento": "pix"})
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["meio_pagamento"] == "pix"


def test_meio_pagamento_invalido_retorna_422(client):
    conta = _criar_conta_corrente(client)
    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 10,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "meio_pagamento": "cheque",
        },
    )
    assert resposta.status_code == 422


def test_pix_parcelado_em_conta_corrente_e_permitido_e_sem_fatura(client):
    """Parcelamento não é exclusivo de cartão de crédito — Pix parcelado
    numa conta corrente é um caso real, e não deve ter fatura nenhuma
    (fatura só existe pra ciclo de fechamento de cartão)."""
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Geladeira via Pix parcelado",
            "valor_total": 900,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-09-05",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    assert resposta.status_code == 201
    parcelas = resposta.json()
    assert len(parcelas) == 3
    assert all(p["fatura_referencia"] is None for p in parcelas)
    assert all(p["meio_pagamento"] == "pix" for p in parcelas)


def test_mover_fatura_manualmente_marca_override(client):
    cartao = _criar_conta_cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    transacao = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
    ).json()
    assert transacao["fatura_referencia"] == "2026-08-08"

    movida = client.patch(f"/transacoes/{transacao['id']}/fatura", json={"fatura_referencia": "2026-09-08"})
    assert movida.status_code == 200
    assert movida.json()["fatura_referencia"] == "2026-09-08"
    assert movida.json()["fatura_override"] is True


def test_excluir_transacao(client):
    cartao = _criar_conta_cartao(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    transacao = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 30,
            "tipo_movimento": "despesa",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
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
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 300.00,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
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
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()

    parcelas = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 30.00,
            "parcela_total": 2,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
    ).json()

    assert parcelas[0]["fatura_referencia"] == "2026-08-08"
    assert parcelas[1]["fatura_referencia"] == "2026-09-08"


# ── busca/filtro em GET /transacoes e GET /transacoes/resumo ──────────────


def test_filtrar_por_categoria(client):
    conta = _criar_conta_corrente(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": mercado["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": lazer["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.get("/transacoes", params={"categoria_id": mercado["id"]})
    assert resposta.status_code == 200
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["categoria_id"] == mercado["id"]


def test_filtrar_por_tipo_movimento(client):
    conta = _criar_conta_corrente(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 5000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 100, "tipo_movimento": "despesa", "conta_id": conta["id"]},
    )

    resposta = client.get("/transacoes", params={"tipo_movimento": "receita"})
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["tipo_movimento"] == "receita"


def test_filtrar_por_periodo(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    payload_base = {
        "tipo_movimento": "despesa",
        "conta_id": conta["id"],
        "categoria_id": categoria["id"],
        "estrutura_custo": "variavel",
        "meio_pagamento": "pix",
    }
    client.post("/transacoes", json={**payload_base, "data_compra": "2026-08-31", "valor": 10})
    client.post("/transacoes", json={**payload_base, "data_compra": "2026-09-15", "valor": 20})
    client.post("/transacoes", json={**payload_base, "data_compra": "2026-10-01", "valor": 30})

    resposta = client.get("/transacoes", params={"data_inicio": "2026-09-01", "data_fim": "2026-09-30"})
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["valor"] == 20


def test_buscar_por_descricao_parcial_case_insensitive(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 40,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
            "descricao": "Supermercado Extra",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 15,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
            "descricao": "Farmácia",
        },
    )

    resposta = client.get("/transacoes", params={"descricao": "extra"})
    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["descricao"] == "Supermercado Extra"


def test_listar_sem_filtro_continua_retornando_tudo(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    payload_base = {
        "tipo_movimento": "despesa",
        "conta_id": conta["id"],
        "categoria_id": categoria["id"],
        "estrutura_custo": "variavel",
        "meio_pagamento": "pix",
    }
    client.post("/transacoes", json={**payload_base, "data_compra": "2026-09-05", "valor": 10})
    client.post("/transacoes", json={**payload_base, "data_compra": "2026-09-06", "valor": 20})

    assert len(client.get("/transacoes").json()) == 2


def test_resumo_sem_filtro_soma_tudo(client):
    conta = _criar_conta_corrente(client)
    categoria = client.post("/categorias", json={"nome": "Categoria Teste"}).json()
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-01", "valor": 5000, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 2000,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resumo = client.get("/transacoes/resumo").json()
    assert resumo["total_lancamentos"] == 2
    assert resumo["receitas"] == 5000
    assert resumo["resultado_saude"] == 3000


def test_resumo_respeita_filtro_de_categoria(client):
    conta = _criar_conta_corrente(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    lazer = client.post("/categorias", json={"nome": "Lazer"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": mercado["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-06",
            "valor": 100,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": lazer["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resumo = client.get("/transacoes/resumo", params={"categoria_id": mercado["id"]}).json()
    assert resumo["total_lancamentos"] == 1
    assert resumo["despesas_brutas"] == 300


def test_resumo_de_outro_usuario_nao_mistura(client, current_user):
    conta = _criar_conta_corrente(client)
    client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 999, "tipo_movimento": "receita", "conta_id": conta["id"]},
    )

    current_user["id"] = OUTRO_USUARIO
    resumo = client.get("/transacoes/resumo").json()
    assert resumo["total_lancamentos"] == 0
    assert resumo["receitas"] == 0


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


def test_receita_com_categoria_de_despesa_retorna_422(client):
    conta = _criar_conta_corrente(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()  # tipo despesa (default)

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 100,
            "tipo_movimento": "receita",
            "conta_id": conta["id"],
            "categoria_id": mercado["id"],
        },
    )
    assert resposta.status_code == 422


def test_aplicacao_com_categoria_de_investimento_e_aceita(client):
    conta = _criar_conta_corrente(client)
    investimentos = client.post("/categorias", json={"nome": "Investimentos", "tipo": "investimento"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "categoria_id": investimentos["id"],
            "estrutura_custo": "investimentos",
        },
    )
    assert resposta.status_code == 201


def test_aplicacao_com_categoria_de_despesa_retorna_422(client):
    conta = _criar_conta_corrente(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 500,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "categoria_id": mercado["id"],
        },
    )
    assert resposta.status_code == 422


def test_despesa_com_caixinha_retorna_422(client):
    conta = _criar_conta_corrente(client)
    caixinha = client.post("/caixinhas", json={"nome": "Reserva"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    assert resposta.status_code == 422


def test_retirada_com_caixinha_e_aceita(client):
    conta = _criar_conta_corrente(client)
    caixinha = client.post("/caixinhas", json={"nome": "Reserva"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "retirada",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    assert resposta.status_code == 201


def test_compra_parcelada_com_categoria_de_receita_retorna_422(client):
    cartao = _criar_conta_cartao(client)
    receita = client.post("/categorias", json={"nome": "Receita", "tipo": "receita"}).json()

    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": "Notebook",
            "valor_total": 300,
            "parcela_total": 3,
            "data_primeira_parcela": "2026-08-05",
            "conta_id": cartao["id"],
            "categoria_id": receita["id"],
        },
    )
    assert resposta.status_code == 422


def test_despesa_sem_categoria_estrutura_ou_meio_pagamento_retorna_422(client):
    conta = _criar_conta_corrente(client)

    resposta = client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 50, "tipo_movimento": "despesa", "conta_id": conta["id"]},
    )
    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["detail"]
    assert "estrutura_custo" in resposta.json()["detail"]
    assert "meio_pagamento" in resposta.json()["detail"]


def test_despesa_com_categoria_estrutura_e_meio_pagamento_e_aceita(client):
    conta = _criar_conta_corrente(client)
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 50,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": mercado["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    assert resposta.status_code == 201


def test_compra_parcelada_sem_categoria_estrutura_ou_meio_pagamento_retorna_422(client):
    cartao = _criar_conta_cartao(client)

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
    assert resposta.status_code == 422


def test_aplicacao_sem_caixinha_e_sem_estrutura_custo_retorna_422(client):
    conta = _criar_conta_corrente(client)

    resposta = client.post(
        "/transacoes",
        json={"data_compra": "2026-09-05", "valor": 300, "tipo_movimento": "aplicacao", "conta_id": conta["id"]},
    )
    assert resposta.status_code == 422
    assert "estrutura_custo" in resposta.json()["detail"]


def test_aplicacao_com_estrutura_investimentos_e_aceita(client):
    conta = _criar_conta_corrente(client)

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "estrutura_custo": "investimentos",
        },
    )
    assert resposta.status_code == 201


def test_aplicacao_em_caixinha_sem_estrutura_custo_e_aceita(client):
    conta = _criar_conta_corrente(client)
    caixinha = client.post("/caixinhas", json={"nome": "Reserva"}).json()

    resposta = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 300,
            "tipo_movimento": "aplicacao",
            "conta_id": conta["id"],
            "caixinha_id": caixinha["id"],
        },
    )
    assert resposta.status_code == 201
