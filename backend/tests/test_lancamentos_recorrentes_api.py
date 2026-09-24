from .conftest import OUTRO_USUARIO


def _conta(client):
    return client.post("/contas", json={"nome": "Conta", "tipo_conta": "corrente"}).json()


def _categoria(client, tipo="despesa"):
    # nome varia por tipo — categoria tem nome único por usuário
    # (categorias_user_id_nome_key); um teste que cria despesa e receita
    # (ex: test_atualizar_para_categoria_de_receita_retorna_422) bateria
    # na constraint se as duas se chamassem "Aluguel"
    nome = "Aluguel" if tipo == "despesa" else f"Aluguel ({tipo})"
    return client.post("/categorias", json={"nome": nome, "tipo": tipo}).json()


def _payload(conta_id, categoria_id, **extra):
    payload = {
        "descricao": "Aluguel",
        "valor": 1500,
        "dia_mes": 5,
        "tipo_movimento": "despesa",
        "conta_id": conta_id,
        "categoria_id": categoria_id,
        "estrutura_custo": "fixo",
        "meio_pagamento": "boleto",
        "data_inicio": "2026-09-01",
    }
    payload.update(extra)
    return payload


# ── CRUD ──────────────────────────────────────────────────────────────────


def test_criar_lancamento_recorrente(client):
    conta = _conta(client)
    categoria = _categoria(client)

    resposta = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"]))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["descricao"] == "Aluguel"
    assert corpo["valor"] == 1500
    assert corpo["ativo"] is True
    assert corpo["data_fim"] is None


def test_criar_com_conta_inexistente_retorna_404(client):
    categoria = _categoria(client)
    resposta = client.post("/lancamentos-recorrentes", json=_payload("00000000-0000-0000-0000-000000000000", categoria["id"]))
    assert resposta.status_code == 404


def test_criar_com_categoria_de_receita_retorna_422(client):
    conta = _conta(client)
    categoria_receita = _categoria(client, tipo="receita")
    resposta = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria_receita["id"]))
    assert resposta.status_code == 422


def test_criar_com_subcategoria_de_outra_categoria_ainda_e_aceita_mas_dono_e_checado(client):
    conta = _conta(client)
    categoria = _categoria(client)
    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(conta["id"], categoria["id"], subcategoria_id="00000000-0000-0000-0000-000000000000"),
    )
    assert resposta.status_code == 404


def test_listar_ordena_por_descricao(client):
    conta = _conta(client)
    categoria = _categoria(client)
    client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"], descricao="Netflix"))
    client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"], descricao="Aluguel"))

    resposta = client.get("/lancamentos-recorrentes").json()
    assert [r["descricao"] for r in resposta] == ["Aluguel", "Netflix"]


def test_atualizar_valor(client):
    conta = _conta(client)
    categoria = _categoria(client)
    criado = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.patch(f"/lancamentos-recorrentes/{criado['id']}", json={"valor": 1600})
    assert resposta.status_code == 200
    assert resposta.json()["valor"] == 1600
    assert resposta.json()["descricao"] == "Aluguel"  # resto não muda


def test_atualizar_para_categoria_de_receita_retorna_422(client):
    conta = _conta(client)
    categoria = _categoria(client)
    categoria_receita = _categoria(client, tipo="receita")
    criado = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.patch(f"/lancamentos-recorrentes/{criado['id']}", json={"categoria_id": categoria_receita["id"]})
    assert resposta.status_code == 422


def test_alternar_ativo(client):
    conta = _conta(client)
    categoria = _categoria(client)
    criado = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.patch(f"/lancamentos-recorrentes/{criado['id']}/ativo", params={"ativo": False})
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False


def test_excluir_remove_da_listagem(client):
    conta = _conta(client)
    categoria = _categoria(client)
    criado = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.delete(f"/lancamentos-recorrentes/{criado['id']}")
    assert resposta.status_code == 204
    assert client.get("/lancamentos-recorrentes").json() == []


def test_recorrente_de_outro_usuario_nao_aparece(client, current_user):
    conta = _conta(client)
    categoria = _categoria(client)
    client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"]))

    current_user["id"] = OUTRO_USUARIO
    assert client.get("/lancamentos-recorrentes").json() == []


# ── tipo_movimento: receita/aplicação/retirada além de despesa ─────────────


def test_criar_recorrente_de_receita(client):
    conta = _conta(client)
    categoria_receita = _categoria(client, tipo="receita")

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_receita["id"],
            descricao="Salário",
            tipo_movimento="receita",
            estrutura_custo=None,
            meio_pagamento=None,
        ),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_movimento"] == "receita"
    # servidor força os dois a null pra receita, mesmo que o cliente mande algo
    assert corpo["estrutura_custo"] is None
    assert corpo["meio_pagamento"] is None


def test_criar_recorrente_de_aplicacao_forca_estrutura_custo_investimentos(client):
    conta = _conta(client)
    categoria_investimento = _categoria(client, tipo="investimento")

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_investimento["id"],
            descricao="Aporte mensal",
            tipo_movimento="aplicacao",
            # cliente manda um valor incoerente de propósito — servidor
            # precisa ignorar e forçar 'investimentos'
            estrutura_custo="fixo",
            meio_pagamento="pix",
        ),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_movimento"] == "aplicacao"
    assert corpo["estrutura_custo"] == "investimentos"
    assert corpo["meio_pagamento"] is None


def test_criar_recorrente_de_retirada(client):
    conta = _conta(client)
    categoria_investimento = _categoria(client, tipo="investimento")

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_investimento["id"],
            descricao="Resgate mensal",
            tipo_movimento="retirada",
            estrutura_custo=None,
            meio_pagamento=None,
        ),
    )
    assert resposta.status_code == 201
    assert resposta.json()["estrutura_custo"] == "investimentos"


def test_criar_despesa_sem_estrutura_custo_retorna_422(client):
    conta = _conta(client)
    categoria = _categoria(client)

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(conta["id"], categoria["id"], estrutura_custo=None),
    )
    assert resposta.status_code == 422


def test_criar_despesa_sem_meio_pagamento_retorna_422(client):
    conta = _conta(client)
    categoria = _categoria(client)

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(conta["id"], categoria["id"], meio_pagamento=None),
    )
    assert resposta.status_code == 422


def test_criar_receita_com_categoria_de_despesa_retorna_422(client):
    conta = _conta(client)
    categoria_despesa = _categoria(client)

    resposta = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_despesa["id"],
            tipo_movimento="receita",
            estrutura_custo=None,
            meio_pagamento=None,
        ),
    )
    assert resposta.status_code == 422


def test_atualizar_tipo_movimento_de_despesa_para_receita_zera_campos_de_despesa(client):
    conta = _conta(client)
    categoria_despesa = _categoria(client)
    categoria_receita = _categoria(client, tipo="receita")
    criado = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria_despesa["id"])).json()

    resposta = client.patch(
        f"/lancamentos-recorrentes/{criado['id']}",
        json={"tipo_movimento": "receita", "categoria_id": categoria_receita["id"]},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["estrutura_custo"] is None
    assert corpo["meio_pagamento"] is None


def test_confirmar_recorrente_de_receita_cria_transacao_do_tipo_certo(client):
    conta = _conta(client)
    categoria_receita = _categoria(client, tipo="receita")
    recorrente = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_receita["id"],
            descricao="Salário",
            tipo_movimento="receita",
            estrutura_custo=None,
            meio_pagamento=None,
        ),
    ).json()

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 201
    transacao = resposta.json()
    assert transacao["tipo_movimento"] == "receita"
    assert transacao["estrutura_custo"] is None
    assert transacao["meio_pagamento"] is None


def test_confirmar_recorrente_de_aplicacao_cria_transacao_do_tipo_certo(client):
    conta = _conta(client)
    categoria_investimento = _categoria(client, tipo="investimento")
    recorrente = client.post(
        "/lancamentos-recorrentes",
        json=_payload(
            conta["id"],
            categoria_investimento["id"],
            descricao="Aporte mensal",
            tipo_movimento="aplicacao",
            estrutura_custo=None,
            meio_pagamento=None,
        ),
    ).json()

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 201
    transacao = resposta.json()
    assert transacao["tipo_movimento"] == "aplicacao"
    assert transacao["estrutura_custo"] == "investimentos"

    # não deve poluir a Estrutura de Custo de despesas — some no bucket investimentos
    estrutura = client.get("/estrutura-custo/2026-09-01").json()
    fixos = next(b for b in estrutura["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos["realizado"] == 0


# ── confirmar (projeção virtual → transação real) ───────────────────────────


def test_confirmar_cria_transacao_real_vinculada(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 201
    transacao = resposta.json()
    assert transacao["tipo_movimento"] == "despesa"
    assert transacao["valor"] == 1500
    assert transacao["data_compra"] == "2026-09-05"  # dia_mes=5
    assert transacao["categoria_id"] == categoria["id"]
    assert transacao["conta_id"] == conta["id"]
    assert transacao["estrutura_custo"] == "fixo"
    assert transacao["meio_pagamento"] == "boleto"

    # aparece na listagem normal de transações, como qualquer despesa
    listagem = client.get("/transacoes").json()
    assert len(listagem) == 1


def test_confirmar_ajusta_dia_alem_do_mes(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post(
        "/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"], dia_mes=31)
    ).json()

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-02-01"})
    assert resposta.status_code == 201
    assert resposta.json()["data_compra"] == "2026-02-28"  # fevereiro não tem 31


def test_confirmar_o_mesmo_mes_duas_vezes_retorna_409(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 409


def test_confirmar_meses_diferentes_do_mesmo_recorrente_funciona(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-10-01"})
    assert resposta.status_code == 201
    assert len(client.get("/transacoes").json()) == 2


def test_confirmar_recorrente_inexistente_retorna_404(client):
    resposta = client.post(
        "/lancamentos-recorrentes/00000000-0000-0000-0000-000000000000/confirmar",
        json={"vigencia_mes": "2026-09-01"},
    )
    assert resposta.status_code == 404


def test_confirmar_sincroniza_item_de_orcamento_existente(client):
    conta = _conta(client)
    categoria = _categoria(client)
    client.post("/orcamentos", json={"vigencia_mes": "2026-09-01", "receita_base": 10000, "percentual_geral": 100})

    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})

    estrutura = client.get("/estrutura-custo/2026-09-01").json()
    fixos = next(b for b in estrutura["buckets"] if b["bucket"] == "custos_fixos")
    assert fixos["realizado"] == 1500


def test_excluir_recorrente_nao_apaga_transacao_ja_confirmada(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    confirmada = client.post(
        f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"}
    ).json()

    client.delete(f"/lancamentos-recorrentes/{recorrente['id']}")

    ainda_existe = client.get(f"/transacoes/{confirmada['id']}")
    assert ainda_existe.status_code == 200


# ── pular (mês "não aplicável" — ex: viajou) ────────────────────────────────


def test_pular_nao_cria_transacao(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["lancamento_recorrente_id"] == recorrente["id"]
    assert corpo["vigencia_mes"] == "2026-09-01"
    assert client.get("/transacoes").json() == []


def test_pular_faz_compromissos_futuros_avancar_pro_proximo_mes(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    resposta = client.get("/dashboard/compromissos-futuros").json()
    assert len(resposta) == 1
    assert resposta[0]["data_compra"] == "2026-10-05"


def test_pular_o_mesmo_mes_duas_vezes_retorna_409(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 409


def test_pular_mes_ja_confirmado_retorna_409(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"})

    resposta = client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})
    assert resposta.status_code == 409


def test_confirmar_mes_ja_pulado_retorna_409(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    resposta = client.post(
        f"/lancamentos-recorrentes/{recorrente['id']}/confirmar", json={"vigencia_mes": "2026-09-01"}
    )
    assert resposta.status_code == 409


def test_pular_recorrente_inexistente_retorna_404(client):
    resposta = client.post(
        "/lancamentos-recorrentes/00000000-0000-0000-0000-000000000000/pular",
        json={"vigencia_mes": "2026-09-01"},
    )
    assert resposta.status_code == 404


def test_desfazer_pular_volta_a_mostrar_o_mes_como_pendente(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    resposta = client.delete(
        f"/lancamentos-recorrentes/{recorrente['id']}/pular", params={"vigencia_mes": "2026-09-01"}
    )
    assert resposta.status_code == 204

    compromissos = client.get("/dashboard/compromissos-futuros").json()
    assert compromissos[0]["data_compra"] == "2026-09-05"  # voltou a ser o mês pendente original


def test_desfazer_pular_mes_que_nao_foi_pulado_retorna_404(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.delete(
        f"/lancamentos-recorrentes/{recorrente['id']}/pular", params={"vigencia_mes": "2026-09-01"}
    )
    assert resposta.status_code == 404


def test_listar_pulados_retorna_vazio_sem_nenhum_pulado(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()

    resposta = client.get(f"/lancamentos-recorrentes/{recorrente['id']}/pulados")
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_pulados_ordenado_por_mes(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-11-01"})
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    resposta = client.get(f"/lancamentos-recorrentes/{recorrente['id']}/pulados").json()
    assert [p["vigencia_mes"] for p in resposta] == ["2026-09-01", "2026-11-01"]


def test_listar_pulados_nao_inclui_pulados_de_outro_recorrente(client):
    conta = _conta(client)
    categoria = _categoria(client)
    r1 = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    r2 = client.post(
        "/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"], descricao="Outro")
    ).json()
    client.post(f"/lancamentos-recorrentes/{r1['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    assert client.get(f"/lancamentos-recorrentes/{r2['id']}/pulados").json() == []


def test_listar_pulados_recorrente_inexistente_retorna_404(client):
    resposta = client.get("/lancamentos-recorrentes/00000000-0000-0000-0000-000000000000/pulados")
    assert resposta.status_code == 404


def test_desfazer_pular_remove_da_listagem(client):
    conta = _conta(client)
    categoria = _categoria(client)
    recorrente = client.post("/lancamentos-recorrentes", json=_payload(conta["id"], categoria["id"])).json()
    client.post(f"/lancamentos-recorrentes/{recorrente['id']}/pular", json={"vigencia_mes": "2026-09-01"})

    client.delete(f"/lancamentos-recorrentes/{recorrente['id']}/pular", params={"vigencia_mes": "2026-09-01"})

    assert client.get(f"/lancamentos-recorrentes/{recorrente['id']}/pulados").json() == []
