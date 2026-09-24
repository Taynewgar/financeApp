"""Popula o Supabase real de um usuário com lançamentos variados, pra testar
telas (Lançamentos, Dashboard, Estrutura de Custo, Planejamento) com dados
mais coerentes do que uns poucos lançamentos manuais soltos. Cobre os 6
tipos de movimento (receita, despesa, aplicação, retirada, estorno,
ressarcimento), varia meio de pagamento/conta pra exercitar filtros, e usa
uma gama ampla de categorias/subcategorias (moradia, mercado, lazer,
transporte, saúde, 2 categorias de investimento) em vez de só um punhado —
pra Gráficos/Estrutura de Custo terem o que agrupar.

Também cria um orçamento encadeado (um por mês, sobra rolando via
/proximo-mes) pros últimos 3 meses + o atual — Aluguel com orçado R$1.000 x
realizado R$1.500 fixo (sobra negativa acumulando), Mercado variando em
torno do orçado, investimento batendo a meta (R$500 aportado x R$400 de
piso). Reaproveita se já existir orçamento pro mês (idempotente, roda de
novo sem duplicar) — mas não é apagado por --limpar (que só mexe em
lançamentos); pra recriar do zero, rode antes
tests/limpar_dados_integracao.py.

Também cria 2 despesas fixas recorrentes (`lancamentos_recorrentes`,
Rodada 20): "Internet" com histórico (2 meses confirmados + 1 pulado, pra
testar a tela de "Meses pulados"/desfazer) e o mês atual pendente;
"Assinatura Streaming" só com o mês atual pendente — juntas garantem mais
de 1 item em Compromissos Futuros ao mesmo tempo.

Não faz parte da suíte automatizada (não roda em CI) — roda contra sua conta
de verdade. Tudo que cria tem descrição prefixada com "[seed]", pra dar pra
identificar e remover depois com --limpar (que só mexe no que tem esse
prefixo — nunca em lançamentos seus).

Requer rede de saída para o Supabase — rode localmente, não em CI.

Uso:
    cd backend
    source venv/bin/activate
    TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste \
        python tests/seed_dados_teste.py

    # pra remover depois:
    TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste \
        python tests/seed_dados_teste.py --limpar
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

PREFIXO = "[seed]"

client = TestClient(app)


def sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_ou_criar(headers: dict, listar_path: str, nome: str, extra: dict | None = None) -> dict:
    """Reaproveita se já existir um registro com esse nome (idempotente —
    rodar o script duas vezes não duplica a base, o que muda são só os
    lançamentos, que ganham datas novas a cada rodada)."""
    existentes = client.get(listar_path, headers=headers).json()
    achado = next((x for x in existentes if x["nome"] == nome), None)
    if achado:
        return achado
    resposta = client.post(listar_path, json={"nome": nome, **(extra or {})}, headers=headers)
    resposta.raise_for_status()
    return resposta.json()


def get_ou_criar_recorrente(headers: dict, descricao: str, extra: dict) -> dict:
    """Mesma ideia de get_ou_criar, mas pra lançamentos_recorrentes — que
    não tem campo "nome" (é "descricao") e vive num endpoint próprio."""
    existentes = client.get("/lancamentos-recorrentes", headers=headers).json()
    achado = next((x for x in existentes if x["descricao"] == descricao), None)
    if achado:
        return achado
    resposta = client.post("/lancamentos-recorrentes", json={"descricao": descricao, **extra}, headers=headers)
    resposta.raise_for_status()
    return resposta.json()


def mes_offset(hoje: date, meses_atras: int) -> tuple[int, int]:
    total = hoje.month - 1 - meses_atras
    return hoje.year + total // 12, total % 12 + 1


def _buscar_orcamento_do_mes(headers: dict, ano: int, mes: int) -> dict | None:
    alvo = f"{ano:04d}-{mes:02d}"
    todos = client.get("/orcamentos", headers=headers).json()
    return next((o for o in todos if o["vigencia_mes"][:7] == alvo), None)


def garantir_orcamento_mes(headers: dict, ano: int, mes: int, sub_aluguel: dict, sub_supermercado: dict, cat_invest: dict) -> dict:
    """Idempotente: se já existe orçamento pra esse mês (desta rodada ou de
    uma anterior), reaproveita. Senão, encadeia via /proximo-mes a partir do
    mês anterior (se existir) — preserva a sobra rolando; senão cria do
    zero com os itens iniciais (só acontece pro mês mais antigo da janela).
    Mesmo cenário usado a sessão inteira pra testar o envelope: Aluguel
    orçado R$1.000 x realizado R$1.500 fixo (sobra -500 acumulando mês a
    mês), Mercado com gasto variável em torno do orçado, investimento
    batendo a meta (R$500 aportado x R$400 de piso)."""
    existente = _buscar_orcamento_do_mes(headers, ano, mes)
    if existente:
        return existente

    total = ano * 12 + (mes - 1) - 1
    ano_anterior, mes_anterior = total // 12, total % 12 + 1
    base = _buscar_orcamento_do_mes(headers, ano_anterior, mes_anterior)
    if base:
        resp = client.post(f"/orcamentos/{base['id']}/proximo-mes", headers=headers)
        resp.raise_for_status()
        return resp.json()

    orcamento = client.post(
        "/orcamentos",
        json={"vigencia_mes": date(ano, mes, 1).isoformat(), "receita_base": 8000, "percentual_geral": 100},
        headers=headers,
    ).json()
    itens = [
        {"bucket": "custos_fixos", "subcategoria_id": sub_aluguel["id"], "orcamento_mensal": 1000},
        {"bucket": "custos_variaveis", "subcategoria_id": sub_supermercado["id"], "orcamento_mensal": 1000},
        {"bucket": "investimentos", "categoria_id": cat_invest["id"], "orcamento_mensal": 400},
    ]
    for item in itens:
        client.post(f"/orcamentos/{orcamento['id']}/itens", json=item, headers=headers)
    return orcamento


def montar_categorias(headers: dict) -> dict:
    """Gama ampla de categorias/subcategorias — não só o mínimo pro
    envelope (Aluguel/Mercado/Investimento) — pra Gráficos, Busca e
    Estrutura de Custo terem várias combinações reais pra agrupar/filtrar,
    em vez de um único ponto de dados por bucket."""
    categorias = {
        "salario": get_ou_criar(headers, "/categorias", "Salário (seed)", {"tipo": "receita"}),
        "freelance": get_ou_criar(headers, "/categorias", "Renda Extra (seed)", {"tipo": "receita"}),
        "moradia": get_ou_criar(headers, "/categorias", "Moradia (seed)", {"tipo": "despesa"}),
        "transporte": get_ou_criar(headers, "/categorias", "Transporte (seed)", {"tipo": "despesa"}),
        "saude": get_ou_criar(headers, "/categorias", "Saúde (seed)", {"tipo": "despesa"}),
        "mercado": get_ou_criar(headers, "/categorias", "Mercado (seed)", {"tipo": "despesa"}),
        "lazer": get_ou_criar(headers, "/categorias", "Lazer (seed)", {"tipo": "despesa"}),
        "invest": get_ou_criar(headers, "/categorias", "Renda Fixa (seed)", {"tipo": "investimento"}),
        "acoes": get_ou_criar(headers, "/categorias", "Ações e Fundos (seed)", {"tipo": "investimento"}),
    }

    def sub(nome: str, cat_key: str, estrutura: str) -> dict:
        return get_ou_criar(
            headers, "/subcategorias", nome,
            {"categoria_id": categorias[cat_key]["id"], "estrutura_custo_padrao": estrutura},
        )

    categorias["sub_aluguel"] = sub("Aluguel (seed)", "moradia", "fixo")
    categorias["sub_condominio"] = sub("Condomínio (seed)", "moradia", "fixo")
    categorias["sub_luz"] = sub("Conta de Luz (seed)", "moradia", "fixo")
    categorias["sub_internet"] = sub("Internet (seed)", "moradia", "fixo")
    categorias["sub_supermercado"] = sub("Supermercado (seed)", "mercado", "variavel")
    categorias["sub_feira"] = sub("Feira (seed)", "mercado", "variavel")
    categorias["sub_streaming"] = sub("Streaming (seed)", "lazer", "variavel")
    categorias["sub_restaurante"] = sub("Restaurante (seed)", "lazer", "variavel")
    categorias["sub_viagem"] = sub("Viagem (seed)", "lazer", "sazonal")
    categorias["sub_combustivel"] = sub("Combustível (seed)", "transporte", "variavel")
    categorias["sub_app_transporte"] = sub("Apps de Transporte (seed)", "transporte", "variavel")
    categorias["sub_plano_saude"] = sub("Plano de Saúde (seed)", "saude", "fixo")
    categorias["sub_farmacia"] = sub("Farmácia (seed)", "saude", "variavel")
    return categorias


def montar_recorrentes(headers: dict, corrente: dict, cartao: dict, cat: dict) -> None:
    """Despesa fixa recorrente (Rodada 20): 2 recorrentes pra exercitar os
    3 estados por mês (confirmado/pulado/pendente) e Compromissos Futuros
    com mais de 1 item ao mesmo tempo. "Internet" já tem histórico (2 meses
    confirmados + 1 pulado, pra testar "Meses pulados"/desfazer) e o mês
    atual pendente; "Assinatura Streaming" só tem o mês atual, também
    pendente."""
    hoje = date.today()
    ano_inicio, mes_inicio = mes_offset(hoje, 3)

    internet = get_ou_criar_recorrente(
        headers, f"{PREFIXO} Internet",
        {
            "valor": 120, "dia_mes": 20, "conta_id": corrente["id"], "categoria_id": cat["moradia"]["id"],
            "subcategoria_id": cat["sub_internet"]["id"], "estrutura_custo": "fixo",
            "meio_pagamento": "debito_automatico", "data_inicio": date(ano_inicio, mes_inicio, 1).isoformat(),
        },
    )
    for meses_atras, acao in [(3, "confirmar"), (2, "pular"), (1, "confirmar")]:
        ano, mes = mes_offset(hoje, meses_atras)
        vigencia = date(ano, mes, 1).isoformat()
        resposta = client.post(
            f"/lancamentos-recorrentes/{internet['id']}/{acao}", json={"vigencia_mes": vigencia}, headers=headers,
        )
        if resposta.status_code not in (201, 409):
            print(f"  falhou recorrente Internet ({acao} {vigencia}) — {resposta.status_code} {resposta.text}")

    ano_atual, mes_atual = mes_offset(hoje, 0)
    get_ou_criar_recorrente(
        headers, f"{PREFIXO} Assinatura Streaming",
        {
            "valor": 45.90, "dia_mes": 5, "conta_id": cartao["id"], "categoria_id": cat["lazer"]["id"],
            "subcategoria_id": cat["sub_streaming"]["id"], "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito", "data_inicio": date(ano_atual, mes_atual, 1).isoformat(),
        },
    )


def montar_massa(headers: dict) -> None:
    corrente = get_ou_criar(headers, "/contas", "Conta Corrente (seed)", {"tipo_conta": "corrente"})
    cartao = get_ou_criar(
        headers, "/contas", "Cartão (seed)",
        {"tipo_conta": "cartao_credito", "dia_fechamento": 5, "dia_vencimento": 12},
    )
    caixinha = get_ou_criar(headers, "/caixinhas", "Reserva de Emergência (seed)")
    cat = montar_categorias(headers)

    hoje = date.today()
    criados = 0

    for meses_atras in range(3, -1, -1):  # últimos 3 meses + o atual
        ano, mes = mes_offset(hoje, meses_atras)
        # orçamento sempre antes dos lançamentos do mês: assim os itens de
        # Aluguel/Mercado/Investimento já existem quando a transação chega,
        # e a sincronização reativa (sincronizar_item_orcamento) não cria
        # item duplicado a R$0 no lugar do item com valor de verdade.
        garantir_orcamento_mes(headers, ano, mes, cat["sub_aluguel"], cat["sub_supermercado"], cat["invest"])

        def d(dia: int, ano=ano, mes=mes) -> str:
            return date(ano, mes, min(dia, 28)).isoformat()

        lancamentos = [
            ("/transacoes", {
                "data_compra": d(5), "valor": 5200, "descricao": f"{PREFIXO} Salário",
                "tipo_movimento": "receita", "conta_id": corrente["id"], "categoria_id": cat["salario"]["id"],
            }),
            ("/transacoes", {
                "data_compra": d(10), "valor": 1500, "descricao": f"{PREFIXO} Aluguel",
                "tipo_movimento": "despesa", "conta_id": corrente["id"], "categoria_id": cat["moradia"]["id"],
                "subcategoria_id": cat["sub_aluguel"]["id"], "estrutura_custo": "fixo",
                "meio_pagamento": "debito_automatico",
            }),
            ("/transacoes", {
                "data_compra": d(8), "valor": round(random.uniform(280, 380), 2),
                "descricao": f"{PREFIXO} Condomínio", "tipo_movimento": "despesa", "conta_id": corrente["id"],
                "categoria_id": cat["moradia"]["id"], "subcategoria_id": cat["sub_condominio"]["id"],
                "estrutura_custo": "fixo", "meio_pagamento": "boleto",
            }),
            ("/transacoes", {
                "data_compra": d(12), "valor": round(random.uniform(140, 220), 2),
                "descricao": f"{PREFIXO} Conta de Luz", "tipo_movimento": "despesa", "conta_id": corrente["id"],
                "categoria_id": cat["moradia"]["id"], "subcategoria_id": cat["sub_luz"]["id"],
                "estrutura_custo": "fixo", "meio_pagamento": "boleto",
            }),
            ("/transacoes", {
                "data_compra": d(7), "valor": 350, "descricao": f"{PREFIXO} Plano de Saúde",
                "tipo_movimento": "despesa", "conta_id": corrente["id"], "categoria_id": cat["saude"]["id"],
                "subcategoria_id": cat["sub_plano_saude"]["id"], "estrutura_custo": "fixo",
                "meio_pagamento": "debito_automatico",
            }),
            ("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(150, 300), 2),
                "descricao": f"{PREFIXO} Combustível", "tipo_movimento": "despesa", "conta_id": corrente["id"],
                "categoria_id": cat["transporte"]["id"], "subcategoria_id": cat["sub_combustivel"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_debito",
            }),
            ("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(60, 150), 2),
                "descricao": f"{PREFIXO} Apps de Transporte", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat["transporte"]["id"], "subcategoria_id": cat["sub_app_transporte"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_credito",
            }),
            ("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(80, 250), 2),
                "descricao": f"{PREFIXO} Restaurante", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat["lazer"]["id"], "subcategoria_id": cat["sub_restaurante"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_credito",
            }),
            ("/transacoes", {
                "data_compra": d(15), "valor": 500, "descricao": f"{PREFIXO} Aporte mensal",
                "tipo_movimento": "aplicacao", "conta_id": corrente["id"], "categoria_id": cat["invest"]["id"],
                "estrutura_custo": "investimentos",
            }),
            ("/transacoes", {
                "data_compra": d(15), "valor": 300, "descricao": f"{PREFIXO} Reserva mensal",
                "tipo_movimento": "aplicacao", "conta_id": corrente["id"], "caixinha_id": caixinha["id"],
            }),
        ]

        if meses_atras in (3, 1):  # renda variável — nem todo mês tem freelance
            lancamentos.append(("/transacoes", {
                "data_compra": d(20), "valor": round(random.uniform(400, 1200), 2),
                "descricao": f"{PREFIXO} Freelance", "tipo_movimento": "receita", "conta_id": corrente["id"],
                "categoria_id": cat["freelance"]["id"],
            }))
        if meses_atras in (2, 0):
            lancamentos.append(("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(40, 90), 2),
                "descricao": f"{PREFIXO} Feira", "tipo_movimento": "despesa", "conta_id": corrente["id"],
                "categoria_id": cat["mercado"]["id"], "subcategoria_id": cat["sub_feira"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "dinheiro",
            }))
        if meses_atras in (3, 0):
            lancamentos.append(("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(35, 120), 2),
                "descricao": f"{PREFIXO} Farmácia", "tipo_movimento": "despesa", "conta_id": corrente["id"],
                "categoria_id": cat["saude"]["id"], "subcategoria_id": cat["sub_farmacia"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_debito",
            }))
        if meses_atras == 2:  # gasto sazonal pontual (o mais alto do período)
            lancamentos.append(("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(1000, 1800), 2),
                "descricao": f"{PREFIXO} Viagem", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat["lazer"]["id"], "subcategoria_id": cat["sub_viagem"]["id"],
                "estrutura_custo": "sazonal", "meio_pagamento": "cartao_credito",
            }))
        if meses_atras in (1, 0):  # segunda categoria de investimento, além da renda fixa
            lancamentos.append(("/transacoes", {
                "data_compra": d(16), "valor": round(random.uniform(200, 600), 2),
                "descricao": f"{PREFIXO} Aporte em Ações", "tipo_movimento": "aplicacao",
                "conta_id": corrente["id"], "categoria_id": cat["acoes"]["id"], "estrutura_custo": "investimentos",
            }))
        if meses_atras == 1:  # retirada pontual da reserva, pra testar o caminho inverso da aplicação
            lancamentos.append(("/transacoes", {
                "data_compra": d(22), "valor": 200, "descricao": f"{PREFIXO} Retirada da reserva",
                "tipo_movimento": "retirada", "conta_id": corrente["id"], "caixinha_id": caixinha["id"],
            }))

        primeiro_supermercado_id = None
        for _ in range(4):
            payload = {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(60, 320), 2),
                "descricao": f"{PREFIXO} Supermercado", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat["mercado"]["id"], "subcategoria_id": cat["sub_supermercado"]["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_credito",
            }
            resposta = client.post("/transacoes", json=payload, headers=headers)
            if resposta.status_code == 201:
                criados += 1
                if primeiro_supermercado_id is None:
                    primeiro_supermercado_id = resposta.json()["id"]
            elif resposta.status_code != 409:
                print(f"  falhou: {payload['descricao']} — {resposta.status_code} {resposta.text}")

        if meses_atras == 2 and primeiro_supermercado_id:  # estorno vinculado a uma compra real
            lancamentos.append(("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(20, 60), 2),
                "descricao": f"{PREFIXO} Estorno Supermercado", "tipo_movimento": "estorno",
                "conta_id": cartao["id"], "categoria_id": cat["mercado"]["id"], "estrutura_custo": "variavel",
                "meio_pagamento": "cartao_credito", "ajuste_de_transacao_id": primeiro_supermercado_id,
            }))
        if meses_atras == 0:  # ressarcimento avulso, sem transação de origem
            lancamentos.append(("/transacoes", {
                "data_compra": d(18), "valor": round(random.uniform(30, 90), 2),
                "descricao": f"{PREFIXO} Reembolso Farmácia", "tipo_movimento": "ressarcimento",
                "conta_id": corrente["id"], "categoria_id": cat["saude"]["id"],
                "subcategoria_id": cat["sub_farmacia"]["id"], "estrutura_custo": "variavel",
                "meio_pagamento": "pix",
            }))

        for path, payload in lancamentos:
            resposta = client.post(path, json=payload, headers=headers)
            if resposta.status_code == 201:
                criados += 1
            elif resposta.status_code != 409:  # 409 = já existe idêntico, seguimos
                print(f"  falhou: {payload.get('descricao')} — {resposta.status_code} {resposta.text}")

    # uma compra parcelada, pra testar a tela com parcelas
    resposta = client.post(
        "/transacoes/parceladas",
        json={
            "descricao": f"{PREFIXO} Notebook", "valor_total": 3600, "parcela_total": 6,
            "data_primeira_parcela": date(hoje.year, hoje.month, 10).isoformat(),
            "conta_id": cartao["id"], "categoria_id": cat["lazer"]["id"], "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers,
    )
    if resposta.status_code == 201:
        criados += len(resposta.json())

    montar_recorrentes(headers, corrente, cartao, cat)

    print(f"{criados} lançamento(s) criado(s) com prefixo \"{PREFIXO}\".")


def limpar(headers: dict) -> None:
    todas = client.get("/transacoes", headers=headers).json()
    alvo = [t for t in todas if (t.get("descricao") or "").startswith(PREFIXO)]
    for t in alvo:
        client.delete(f"/transacoes/{t['id']}", headers=headers)

    recorrentes = client.get("/lancamentos-recorrentes", headers=headers).json()
    alvo_recorrentes = [r for r in recorrentes if (r.get("descricao") or "").startswith(PREFIXO)]
    for r in alvo_recorrentes:
        client.delete(f"/lancamentos-recorrentes/{r['id']}", headers=headers)

    print(f"{len(alvo)} lançamento(s) e {len(alvo_recorrentes)} recorrente(s) de seed removido(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limpar", action="store_true", help="remove só os lançamentos criados por este script")
    args = parser.parse_args()

    email = os.environ.get("TEST_USER_EMAIL")
    password = os.environ.get("TEST_USER_PASSWORD")
    if not email or not password or not settings.supabase_url:
        sys.exit("Defina TEST_USER_EMAIL/TEST_USER_PASSWORD e backend/.env (mesmo usuário dos testes de integração).")

    headers = {"Authorization": f"Bearer {sign_in(email, password)}"}

    if args.limpar:
        limpar(headers)
    else:
        montar_massa(headers)


if __name__ == "__main__":
    main()
