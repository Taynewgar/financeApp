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


def test_mover_subcategoria_para_outra_categoria_despesa(client):
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    casa = client.post("/categorias", json={"nome": "Casa"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": mercado["id"], "nome": "Feira"}).json()

    movida = client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": casa["id"]})
    assert movida.status_code == 200
    assert movida.json()["categoria_id"] == casa["id"]


def test_mover_subcategoria_atualiza_categoria_em_transacoes_existentes(client):
    # achado 2026-11-03 (bug urgente): mover a subcategoria só atualizava
    # subcategorias.categoria_id — a transação já lançada ficava presa na
    # categoria pai antiga (denormalizada em transacoes.categoria_id),
    # sumindo do filtro pela categoria nova.
    pessoais = client.post("/categorias", json={"nome": "Pessoais"}).json()
    espiritualidade = client.post("/categorias", json={"nome": "Espiritualidade"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": pessoais["id"], "nome": "Trabalhos e Ebós"}).json()
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente", "saldo_inicial": 0}).json()
    transacao = client.post(
        "/transacoes",
        json={
            "data_compra": "2026-11-01",
            "valor": 500,
            "descricao": "Ebó",
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": pessoais["id"],
            "subcategoria_id": sub["id"],
            "estrutura_custo": "sazonal",
            "meio_pagamento": "pix",
        },
    ).json()

    client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": espiritualidade["id"]})

    atualizada = client.get(f"/transacoes/{transacao['id']}").json()
    assert atualizada["categoria_id"] == espiritualidade["id"]


def test_mover_subcategoria_atualiza_categoria_em_recorrentes_existentes(client):
    pessoais = client.post("/categorias", json={"nome": "Pessoais"}).json()
    espiritualidade = client.post("/categorias", json={"nome": "Espiritualidade"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": pessoais["id"], "nome": "Trabalhos e Ebós"}).json()
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente", "saldo_inicial": 0}).json()
    recorrente = client.post(
        "/lancamentos-recorrentes",
        json={
            "descricao": "Ebó mensal",
            "valor": 200,
            "dia_mes": 1,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": pessoais["id"],
            "subcategoria_id": sub["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
            "data_inicio": "2026-11-01",
        },
    ).json()

    client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": espiritualidade["id"]})

    atualizado = client.get(f"/lancamentos-recorrentes/{recorrente['id']}").json()
    assert atualizado["categoria_id"] == espiritualidade["id"]


def test_mover_subcategoria_atualiza_categoria_em_itens_de_orcamento_existentes(client):
    pessoais = client.post("/categorias", json={"nome": "Pessoais"}).json()
    espiritualidade = client.post("/categorias", json={"nome": "Espiritualidade"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": pessoais["id"], "nome": "Trabalhos e Ebós"}).json()
    orcamento = client.post(
        "/orcamentos", json={"vigencia_mes": "2026-11-01", "receita_base": 10000, "percentual_geral": 90}
    ).json()
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "sazonalidades", "categoria_id": pessoais["id"], "subcategoria_id": sub["id"], "orcamento_mensal": 300},
    ).json()

    client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": espiritualidade["id"]})

    itens = client.get(f"/orcamentos/{orcamento['id']}/itens").json()
    item_atualizado = next(i for i in itens if i["id"] == item["id"])
    assert item_atualizado["categoria_id"] == espiritualidade["id"]


def test_mover_subcategoria_para_categoria_receita_retorna_422(client):
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    receita = client.post("/categorias", json={"nome": "Salário", "tipo": "receita"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": mercado["id"], "nome": "Feira"}).json()

    resposta = client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": receita["id"]})
    assert resposta.status_code == 422


def test_mover_subcategoria_para_categoria_inexistente_retorna_404(client):
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": mercado["id"], "nome": "Feira"}).json()

    resposta = client.patch(
        f"/subcategorias/{sub['id']}",
        json={"categoria_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resposta.status_code == 404


def test_mover_subcategoria_para_categoria_de_outro_usuario_retorna_404(client, current_user):
    mercado = client.post("/categorias", json={"nome": "Mercado"}).json()
    sub = client.post("/subcategorias", json={"categoria_id": mercado["id"], "nome": "Feira"}).json()

    current_user["id"] = OUTRO_USUARIO
    categoria_alheia = client.post("/categorias", json={"nome": "Categoria do usuário B"}).json()
    current_user["id"] = "11111111-1111-1111-1111-111111111111"  # volta pro usuário padrão do fixture

    resposta = client.patch(f"/subcategorias/{sub['id']}", json={"categoria_id": categoria_alheia["id"]})
    assert resposta.status_code == 404


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
