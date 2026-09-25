from .conftest import OUTRO_USUARIO


def _criar_orcamento(client, vigencia_mes="2026-09-01", **extra):
    # receita_base/percentual_geral folgados por padrão — dão teto grande o
    # bastante pra qualquer valor de item usado nos testes que não estão
    # testando a validação de teto em si (esses passam valores explícitos)
    payload = {"vigencia_mes": vigencia_mes, "receita_base": 100000, "percentual_geral": 100, **extra}
    return client.post("/orcamentos", json=payload).json()


def test_criar_orcamento_e_listar(client):
    resposta = client.post(
        "/orcamentos",
        json={"vigencia_mes": "2026-09-01", "receita_base": 5000, "percentual_geral": 100},
    )
    assert resposta.status_code == 201
    orcamento = resposta.json()
    assert orcamento["receita_base"] == 5000
    assert orcamento["limite_custos_fixos"] == 40  # default do schema

    listagem = client.get("/orcamentos")
    assert listagem.status_code == 200
    assert any(o["id"] == orcamento["id"] for o in listagem.json())


def test_criar_orcamento_normaliza_vigencia_para_primeiro_dia_do_mes(client):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-15")
    assert orcamento["vigencia_mes"] == "2026-09-01"


def test_criar_orcamento_alimenta_itens_das_categorias_ja_lancadas_no_mes(client):
    """Lançar antes de planejar é o fluxo comum — ao criar o orçamento, as
    categorias/subcategorias já usadas em transações daquele mês viram
    item com orcamento_mensal=0 (você só ajusta o valor), mesma paridade
    retroativa que a sincronização reativa já dá pra transação nova."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    subcategoria = client.post(
        "/subcategorias", json={"categoria_id": categoria["id"], "nome": "Aluguel"}
    ).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "subcategoria_id": subcategoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    orcamento = _criar_orcamento(client)
    itens = client.get(f"/orcamentos/{orcamento['id']}/itens").json()
    assert len(itens) == 1
    assert itens[0]["subcategoria_id"] == subcategoria["id"]
    assert itens[0]["bucket"] == "custos_fixos"
    assert itens[0]["orcamento_mensal"] == 0


def test_criar_orcamento_nao_duplica_item_de_transacao_de_outro_mes(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-05",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    orcamento = _criar_orcamento(client)  # setembro — a transação é de agosto
    itens = client.get(f"/orcamentos/{orcamento['id']}/itens").json()
    assert itens == []


def test_criar_orcamento_sem_campo_obrigatorio_retorna_422(client):
    resposta = client.post("/orcamentos", json={})
    assert resposta.status_code == 422


def test_criar_orcamento_duplicado_no_mesmo_mes_retorna_409(client):
    _criar_orcamento(client, vigencia_mes="2026-09-01")

    repetido = client.post("/orcamentos", json={"vigencia_mes": "2026-09-20"})
    assert repetido.status_code == 409


def test_orcamentos_de_meses_diferentes_nao_conflitam(client):
    primeiro = client.post("/orcamentos", json={"vigencia_mes": "2026-09-01"})
    segundo = client.post("/orcamentos", json={"vigencia_mes": "2026-10-01"})
    assert primeiro.status_code == 201
    assert segundo.status_code == 201


def test_atualizar_orcamento(client):
    orcamento = _criar_orcamento(client)

    atualizado = client.patch(f"/orcamentos/{orcamento['id']}", json={"receita_base": 6000})
    assert atualizado.status_code == 200
    assert atualizado.json()["receita_base"] == 6000


def test_editar_orcamento_inexistente_retorna_404(client):
    resposta = client.patch(
        "/orcamentos/00000000-0000-0000-0000-000000000000",
        json={"receita_base": 1000},
    )
    assert resposta.status_code == 404


def test_usuario_nao_ve_orcamento_de_outro_usuario(client, current_user):
    orcamento = _criar_orcamento(client)

    current_user["id"] = OUTRO_USUARIO
    listagem = client.get("/orcamentos")
    assert not any(o["id"] == orcamento["id"] for o in listagem.json())

    busca = client.get(f"/orcamentos/{orcamento['id']}")
    assert busca.status_code == 404


def test_criar_item_vinculado_a_categoria_existente(client):
    orcamento = _criar_orcamento(client)
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1500},
    )
    assert resposta.status_code == 201
    item = resposta.json()
    assert item["orcamento_id"] == orcamento["id"]
    assert item["categoria_id"] == categoria["id"]
    assert item["ativo"] is True


def test_criar_item_sem_categoria_com_nome_livre_e_valido(client):
    orcamento = _criar_orcamento(client)

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Liberdade Financeira", "orcamento_mensal": 800},
    )
    assert resposta.status_code == 201
    assert resposta.json()["categoria_id"] is None


def test_criar_item_com_categoria_inexistente_retorna_404(client):
    orcamento = _criar_orcamento(client)

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resposta.status_code == 404


def test_criar_item_com_categoria_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)
    categoria = client.post("/categorias", json={"nome": "Moradia"}).json()

    current_user["id"] = OUTRO_USUARIO
    outro_orcamento = _criar_orcamento(client)
    resposta = client.post(
        f"/orcamentos/{outro_orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"]},
    )
    assert resposta.status_code == 404


def test_criar_item_com_conta_vinculada_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)
    conta = client.post("/contas", json={"nome": "Reserva", "tipo_conta": "investimento"}).json()

    current_user["id"] = OUTRO_USUARIO
    outro_orcamento = _criar_orcamento(client)
    resposta = client.post(
        f"/orcamentos/{outro_orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Reserva", "conta_vinculada_id": conta["id"]},
    )
    assert resposta.status_code == 404


def test_criar_item_em_orcamento_inexistente_retorna_404(client):
    resposta = client.post(
        "/orcamentos/00000000-0000-0000-0000-000000000000/itens",
        json={"bucket": "custos_fixos", "nome": "X"},
    )
    assert resposta.status_code == 404


def test_criar_item_em_orcamento_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client)

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Invasão"},
    )
    assert resposta.status_code == 404


def test_listar_itens_de_um_orcamento(client):
    orcamento = _criar_orcamento(client)
    client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"})
    client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "investimentos", "nome": "Reserva"})

    outro_orcamento = _criar_orcamento(client, vigencia_mes="2026-10-01")
    client.post(f"/orcamentos/{outro_orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Outro mês"})

    listagem = client.get(f"/orcamentos/{orcamento['id']}/itens")
    assert listagem.status_code == 200
    nomes = {item["nome"] for item in listagem.json()}
    assert nomes == {"Aluguel", "Reserva"}


def test_atualizar_item(client):
    orcamento = _criar_orcamento(client)
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1000}
    ).json()

    atualizado = client.patch(
        f"/orcamentos/{orcamento['id']}/itens/{item['id']}", json={"orcamento_mensal": 1200}
    )
    assert atualizado.status_code == 200
    assert atualizado.json()["orcamento_mensal"] == 1200


def test_atualizar_item_inexistente_retorna_404(client):
    orcamento = _criar_orcamento(client)

    resposta = client.patch(
        f"/orcamentos/{orcamento['id']}/itens/00000000-0000-0000-0000-000000000000",
        json={"orcamento_mensal": 100},
    )
    assert resposta.status_code == 404


def test_desativar_item_nao_exclui(client):
    orcamento = _criar_orcamento(client)
    item = client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"}).json()

    desativado = client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}/ativo", params={"ativo": False})
    assert desativado.status_code == 200
    assert desativado.json()["ativo"] is False

    listagem = client.get(f"/orcamentos/{orcamento['id']}/itens")
    assert any(i["id"] == item["id"] for i in listagem.json())


def test_usuario_nao_atualiza_item_de_orcamento_de_outro_usuario(client, current_user):
    orcamento = _criar_orcamento(client)
    item = client.post(f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel"}).json()

    current_user["id"] = OUTRO_USUARIO
    resposta = client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}", json={"orcamento_mensal": 1})
    assert resposta.status_code == 404


# ── modelo de envelope acumulativo: POST /orcamentos/{id}/proximo-mes ──────


def test_item_recem_criado_tem_saldo_anterior_zero_e_disponivel_igual_ao_mensal(client):
    orcamento = _criar_orcamento(client)
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1500}
    ).json()

    assert item["saldo_anterior"] == 0
    assert item["disponivel"] == 1500


def test_proximo_mes_carrega_sobra_quando_gasta_menos_que_planejado(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Restaurante"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria["id"], "orcamento_mensal": 400},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 310,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    resposta = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes")
    assert resposta.status_code == 201
    proximo = resposta.json()
    assert proximo["vigencia_mes"] == "2026-10-01"

    novo_item = client.get(f"/orcamentos/{proximo['id']}/itens").json()[0]
    assert novo_item["orcamento_mensal"] == 400  # o valor-base recorrente nunca muda
    assert novo_item["saldo_anterior"] == 90
    assert novo_item["disponivel"] == 490


def test_proximo_mes_carrega_deficit_quando_gasta_mais_que_planejado(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Mercado"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria["id"], "orcamento_mensal": 400},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    novo_item = client.get(f"/orcamentos/{proximo['id']}/itens").json()[0]
    assert novo_item["saldo_anterior"] == -100
    assert novo_item["disponivel"] == 300


def test_saldo_anterior_se_atualiza_sozinho_sem_precisar_gerar_de_novo(client):
    """O bug reportado: saldo_anterior só era calculado no momento de
    "gerar próximo mês" e ficava congelado depois — editar/lançar algo no
    mês anterior DEPOIS de já ter gerado o seguinte não refletia em lugar
    nenhum até alguém gerar de novo (destrutivo: apaga ajustes manuais do
    orçamento já gerado). Agora a leitura recalcula sempre."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-08-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    item_setembro = client.get(f"/orcamentos/{proximo['id']}/itens").json()[0]
    assert item_setembro["saldo_anterior"] == -500  # 1000 planejado - 1500 gasto

    # "correção tardia" — lança mais uma despesa em agosto DEPOIS de já ter
    # gerado o orçamento de setembro, sem regenerar nada
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-20",
            "valor": 500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    item_setembro_de_novo = client.get(f"/orcamentos/{proximo['id']}/itens").json()[0]
    assert item_setembro_de_novo["saldo_anterior"] == -1000  # 1000 - 2000 agora
    assert item_setembro_de_novo["disponivel"] == 0


def test_saldo_anterior_recalcula_em_cadeia_por_varios_meses(client):
    """saldo_anterior_ao_vivo é recursivo — sobe até o primeiro mês da
    cadeia a cada leitura, em vez de confiar numa sobra já acumulada e
    congelada nos meses do meio. Julho (700 gasto de 1000) -> agosto
    (1500 gasto de 1000, com a sobra de julho de +300 no envelope) ->
    setembro: saldo_anterior tem que refletir os dois hops."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()
    julho = _criar_orcamento(client, vigencia_mes="2026-07-01")
    client.post(
        f"/orcamentos/{julho['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-07-10",
            "valor": 700,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    agosto = client.post(f"/orcamentos/{julho['id']}/proximo-mes").json()
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-08-10",
            "valor": 1500,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    setembro = client.post(f"/orcamentos/{agosto['id']}/proximo-mes").json()

    item_setembro = client.get(f"/orcamentos/{setembro['id']}/itens").json()[0]
    # agosto: disponível = 1000 (orçado) + 300 (sobra de julho) = 1300;
    # gastou 1500 -> setembro herda 1300 - 1500 = -200
    assert item_setembro["saldo_anterior"] == -200


def test_proximo_mes_de_item_de_subcategoria_nao_soma_gasto_de_outra_subcategoria_da_mesma_categoria(client):
    """Sobra/déficit de um item de subcategoria tem que olhar só a
    subcategoria dele — não a categoria pai inteira. Cobre a mesma
    prioridade de _chave usada em Estrutura de Custo: categoria_id e
    subcategoria_id vêm preenchidos juntos num lançamento real."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Lazer"}).json()
    viagens = client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Viagens"}).json()
    cinema = client.post("/subcategorias", json={"categoria_id": categoria["id"], "nome": "Cinema"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "subcategoria_id": viagens["id"], "orcamento_mensal": 400},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-10",
            "valor": 300,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "subcategoria_id": viagens["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-12",
            "valor": 1000,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "subcategoria_id": cinema["id"],
            "estrutura_custo": "variavel",
            "meio_pagamento": "pix",
        },
    )

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    itens = client.get(f"/orcamentos/{proximo['id']}/itens").json()
    item_viagens = next(i for i in itens if i["subcategoria_id"] == viagens["id"])
    # sobrou 100 (400 - 300) considerando só Viagens; se Cinema entrasse na
    # conta (bug antigo: filtrava por categoria_id, ignorando subcategoria),
    # o item de Viagens fecharia com déficit de -900 (400 - 1300)
    assert item_viagens["saldo_anterior"] == 100
    assert item_viagens["disponivel"] == 500


def test_proximo_mes_item_sem_vinculo_rola_o_valor_cheio(client):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "investimentos", "nome": "Reserva", "orcamento_mensal": 200},
    )

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    novo_item = client.get(f"/orcamentos/{proximo['id']}/itens").json()[0]
    assert novo_item["saldo_anterior"] == 200
    assert novo_item["disponivel"] == 400


def test_proximo_mes_alimenta_itens_de_transacoes_ja_lancadas_no_mes_seguinte(client):
    """Lançamento feito no mês seguinte antes de gerar o orçamento dele
    (ex: assinatura já cobrada em outubro enquanto setembro ainda está
    aberto) também vira item com valor 0, mesma regra da criação direta."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Streaming"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-10-03",
            "valor": 40,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    itens = client.get(f"/orcamentos/{proximo['id']}/itens").json()
    assert len(itens) == 1
    assert itens[0]["categoria_id"] == categoria["id"]
    assert itens[0]["orcamento_mensal"] == 0


def test_proximo_mes_ignora_item_desativado(client):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Antigo", "orcamento_mensal": 100}
    ).json()
    client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}/ativo", params={"ativo": False})

    proximo = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()
    assert client.get(f"/orcamentos/{proximo['id']}/itens").json() == []


def test_proximo_mes_chamado_duas_vezes_retorna_409_na_segunda(client):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")

    primeira = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes")
    assert primeira.status_code == 201

    repetida = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes")
    assert repetida.status_code == 409


def test_proximo_mes_de_orcamento_de_outro_usuario_retorna_404(client, current_user):
    orcamento = _criar_orcamento(client, vigencia_mes="2026-09-01")

    current_user["id"] = OUTRO_USUARIO
    resposta = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes")
    assert resposta.status_code == 404


def test_proximo_mes_com_substituir_recria_o_orcamento_existente(client):
    setembro = _criar_orcamento(client, vigencia_mes="2026-09-01")
    outubro_antigo = client.post(f"/orcamentos/{setembro['id']}/proximo-mes").json()
    item_antigo = client.post(
        f"/orcamentos/{outubro_antigo['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Vai sumir", "orcamento_mensal": 100},
    ).json()

    resposta = client.post(f"/orcamentos/{setembro['id']}/proximo-mes", params={"substituir": "true"})
    assert resposta.status_code == 201
    outubro_novo = resposta.json()
    assert outubro_novo["vigencia_mes"] == "2026-10-01"
    assert outubro_novo["id"] != outubro_antigo["id"]  # é um orçamento novo, não o mesmo editado

    # o orçamento antigo (e o item criado nele) não existem mais
    assert client.get(f"/orcamentos/{outubro_antigo['id']}").status_code == 404
    assert client.get(f"/orcamentos/{outubro_antigo['id']}/itens").status_code == 404
    assert not any(i["id"] == item_antigo["id"] for i in client.get(f"/orcamentos/{outubro_novo['id']}/itens").json())


# ── teto por bucket (regra 1: renda × percentual_geral × limite_bucket) ────
# mesmo exemplo usado na conversa: renda 15000, percentual_geral 90%,
# limite_custos_fixos 40% (default) → teto de custos_fixos = 5400


def _criar_orcamento_do_exemplo(client, vigencia_mes="2026-09-01"):
    return _criar_orcamento(client, vigencia_mes=vigencia_mes, receita_base=15000, percentual_geral=90)


def test_item_expoe_as_duas_leituras_de_percentual(client):
    orcamento = _criar_orcamento_do_exemplo(client)
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()

    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1600},
    ).json()

    assert item["percentual_da_renda"] == 10.67  # 1600 / 15000 * 100
    assert item["percentual_do_teto"] == 29.63  # 1600 / 5400 * 100


def test_itens_dentro_do_teto_do_bucket_sao_aceitos(client):
    orcamento = _criar_orcamento_do_exemplo(client)

    aluguel = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 1600},
    )
    condominio = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Condomínio", "orcamento_mensal": 900},
    )
    assert aluguel.status_code == 201
    assert condominio.status_code == 201  # soma 2500, teto do bucket é 5400


def test_criar_item_que_estoura_teto_do_bucket_retorna_422(client):
    orcamento = _criar_orcamento_do_exemplo(client)
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 5000},
    )

    resposta = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Condomínio", "orcamento_mensal": 500},
    )
    assert resposta.status_code == 422  # 5000 + 500 = 5500 > teto de 5400


def test_atualizar_item_que_estoura_teto_do_bucket_retorna_422(client):
    orcamento = _criar_orcamento_do_exemplo(client)
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 3000},
    )
    condominio = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Condomínio", "orcamento_mensal": 1000},
    ).json()

    resposta = client.patch(
        f"/orcamentos/{orcamento['id']}/itens/{condominio['id']}", json={"orcamento_mensal": 3000}
    )
    assert resposta.status_code == 422  # 3000 (aluguel) + 3000 (novo condomínio) = 6000 > 5400


def test_atualizar_item_para_o_proprio_valor_atual_nao_estoura(client):
    """Editar um item sem mudar o quanto ele consome do teto (ex: só o
    nome) não deve ser bloqueado por reconferir a soma do bucket."""
    orcamento = _criar_orcamento_do_exemplo(client)
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Aluguel", "orcamento_mensal": 5400},
    ).json()

    resposta = client.patch(f"/orcamentos/{orcamento['id']}/itens/{item['id']}", json={"orcamento_mensal": 5400})
    assert resposta.status_code == 200


def test_reativar_item_que_estoura_teto_do_bucket_retorna_422(client):
    orcamento = _criar_orcamento_do_exemplo(client)
    antigo = client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Antigo", "orcamento_mensal": 5000},
    ).json()
    client.patch(f"/orcamentos/{orcamento['id']}/itens/{antigo['id']}/ativo", params={"ativo": False})
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Novo", "orcamento_mensal": 5000},
    )

    resposta = client.patch(f"/orcamentos/{orcamento['id']}/itens/{antigo['id']}/ativo", params={"ativo": True})
    assert resposta.status_code == 422  # 5000 (novo) + 5000 (reativado) = 10000 > 5400


def test_item_com_orcamento_zero_e_receita_base_zero_nao_gera_erro_de_divisao(client):
    orcamento = _criar_orcamento(client, receita_base=0, percentual_geral=0)
    item = client.post(
        f"/orcamentos/{orcamento['id']}/itens", json={"bucket": "custos_fixos", "nome": "Vazio", "orcamento_mensal": 0}
    )
    assert item.status_code == 201
    assert item.json()["percentual_da_renda"] == 0.0
    assert item.json()["percentual_do_teto"] == 0.0


def test_sobra_acumulada_do_bucket_amplia_o_teto_para_novos_itens(client):
    """O exemplo combinado: Fixo sobrou R$200 no total (soma dos itens),
    então o teto efetivo desse mês para alocar itens em Fixo é o teto puro
    + essa sobra — não só o teto puro sozinho."""
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()

    setembro = _criar_orcamento_do_exemplo(client, vigencia_mes="2026-09-01")  # teto_custos_fixos = 5400
    client.post(
        f"/orcamentos/{setembro['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 800,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    outubro = client.post(f"/orcamentos/{setembro['id']}/proximo-mes").json()
    # outubro nasce com o item de Aluguel carregando saldo_anterior = 200 (1000 - 800)

    sem_sobra = client.post(
        f"/orcamentos/{outubro['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Novo item", "orcamento_mensal": 5400},
    )
    assert sem_sobra.status_code == 422  # 1000 (aluguel) + 5400 = 6400 > 5400 (teto puro, sem sobra)

    com_sobra = client.post(
        f"/orcamentos/{outubro['id']}/itens",
        json={"bucket": "custos_fixos", "nome": "Novo item", "orcamento_mensal": 4600},
    )
    assert com_sobra.status_code == 201  # 1000 + 4600 = 5600 ≤ 5600 (5400 teto puro + 200 de sobra)


def test_estrutura_custo_expoe_saldo_anterior_acumulado_por_bucket(client):
    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria = client.post("/categorias", json={"nome": "Aluguel"}).json()

    setembro = _criar_orcamento_do_exemplo(client, vigencia_mes="2026-09-01")
    client.post(
        f"/orcamentos/{setembro['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria["id"], "orcamento_mensal": 1000},
    )
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-05",
            "valor": 800,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    client.post(f"/orcamentos/{setembro['id']}/proximo-mes")

    resposta = client.get("/estrutura-custo/2026-10-01").json()
    fixos = next(b for b in resposta["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos["saldo_anterior_acumulado"] == 200

    # correção tardia em setembro, depois de outubro já gerado — Estrutura
    # de Custo também recalcula ao vivo, não só o endpoint de orçamentos
    client.post(
        "/transacoes",
        json={
            "data_compra": "2026-09-20",
            "valor": 300,
            "tipo_movimento": "despesa",
            "conta_id": conta["id"],
            "categoria_id": categoria["id"],
            "estrutura_custo": "fixo",
            "meio_pagamento": "pix",
        },
    )
    resposta_atualizada = client.get("/estrutura-custo/2026-10-01").json()
    fixos_atualizado = next(b for b in resposta_atualizada["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos_atualizado["saldo_anterior_acumulado"] == -100


def test_listar_itens_busca_dados_em_lote_nao_recalcula_cadeia_item_a_item(client, db_store):
    """Perf (item 24 do backlog, mesma classe de bug já corrigida em
    Estrutura de Custo — Rodada 27 — e em /graficos — Rodada 2026-09-22).
    Antes, `_enriquecer_item()` chamava `saldo_anterior_ao_vivo()` por item
    do orçamento, recursiva, subindo a cadeia de meses anteriores no banco
    a cada passo: uma lista de N itens virava N cadeias de idas e voltas
    sequenciais ao Supabase. Agora usa o mesmo helper de carregamento em
    lote que Estrutura de Custo já usava (`carregar_dados_periodo`): tem
    que ficar num número FIXO de chamadas por requisição, não crescer com
    o histórico nem com o número de itens. Não é o mesmo total de 3 de
    Estrutura de Custo — `listar_itens` também busca sua própria lista
    completa de itens (incluindo inativos, que a tela precisa mostrar; o
    lote carregado por `carregar_dados_periodo` só tem os ativos, usado só
    pra recalcular a cadeia de saldo_anterior) e resolve o orçamento pelo
    id antes de saber a vigência — daí 2 chamadas a `orcamentos` e 2 a
    `orcamento_itens` em vez de 1, mas continua fixo, não `O(itens×meses)`."""
    from app.auth import get_db
    from app.main import app

    from .fakes import FakeSupabaseClient

    conta = client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()
    categoria_a = client.post("/categorias", json={"nome": "Aluguel"}).json()
    categoria_b = client.post("/categorias", json={"nome": "Mercado"}).json()
    orcamento = _criar_orcamento(client, vigencia_mes="2026-01-01")
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_fixos", "categoria_id": categoria_a["id"], "orcamento_mensal": 1000},
    )
    client.post(
        f"/orcamentos/{orcamento['id']}/itens",
        json={"bucket": "custos_variaveis", "categoria_id": categoria_b["id"], "orcamento_mensal": 500},
    )
    # encadeia 6 meses via "gerar próximo mês" (jan-jun) — é isso que faz a
    # cadeia de saldo_anterior existir de verdade pros 2 itens
    for mes in range(1, 6):
        for categoria, valor in [(categoria_a, 700), (categoria_b, 300)]:
            client.post(
                "/transacoes",
                json={
                    "data_compra": f"2026-{mes:02d}-05",
                    "valor": valor,
                    "tipo_movimento": "despesa",
                    "conta_id": conta["id"],
                    "categoria_id": categoria["id"],
                    "estrutura_custo": "fixo" if categoria is categoria_a else "variavel",
                    "meio_pagamento": "pix",
                },
            )
        orcamento = client.post(f"/orcamentos/{orcamento['id']}/proximo-mes").json()

    class _ContadorClient:
        def __init__(self, store):
            self._inner = FakeSupabaseClient(store)
            self.chamadas: list[str] = []

        def table(self, nome):
            self.chamadas.append(nome)
            return self._inner.table(nome)

        def rpc(self, nome, params):
            self.chamadas.append(nome)
            return self._inner.rpc(nome, params)

    # pede os itens do ÚLTIMO mês da cadeia — pior caso pra recursão item a
    # item (precisa subir os 5 meses anteriores pra cada um dos 2 itens)
    contador = _ContadorClient(db_store)
    app.dependency_overrides[get_db] = lambda: contador
    try:
        resposta = client.get(f"/orcamentos/{orcamento['id']}/itens")
    finally:
        app.dependency_overrides[get_db] = lambda: FakeSupabaseClient(db_store)

    assert resposta.status_code == 200
    itens = resposta.json()
    assert len(itens) == 2
    assert all(item["saldo_anterior"] != 0 for item in itens)  # cadeia foi de fato calculada
    # 5 no total, fixo — não cresce com o histórico (5 meses) nem com o
    # número de itens (2); sem o fix seriam dezenas de chamadas (2 itens ×
    # ~5 meses de cadeia × 3 queries cada). Transações vêm de 1 RPC
    # agregada (saldo_transacoes_agregado), não de .table("transacoes").
    assert contador.chamadas.count("orcamentos") == 2
    assert contador.chamadas.count("orcamento_itens") == 2
    assert contador.chamadas.count("saldo_transacoes_agregado") == 1
    assert len(contador.chamadas) == 5
