"""Popula o Supabase real de um usuário com lançamentos variados, pra testar
telas (Lançamentos, Dashboard, Estrutura de Custo, Planejamento) com dados
mais coerentes do que uns poucos lançamentos manuais soltos.

Também cria um orçamento encadeado (um por mês, sobra rolando via
/proximo-mes) pros últimos 3 meses + o atual — Aluguel com orçado R$1.000 x
realizado R$1.500 fixo (sobra negativa acumulando), Mercado variando em
torno do orçado, investimento batendo a meta (R$500 aportado x R$400 de
piso). Reaproveita se já existir orçamento pro mês (idempotente, roda de
novo sem duplicar) — mas não é apagado por --limpar (que só mexe em
lançamentos); pra recriar do zero, rode antes
tests/limpar_dados_integracao.py.

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


def montar_massa(headers: dict) -> None:
    corrente = get_ou_criar(headers, "/contas", "Conta Corrente (seed)", {"tipo_conta": "corrente"})
    cartao = get_ou_criar(
        headers, "/contas", "Cartão (seed)",
        {"tipo_conta": "cartao_credito", "dia_fechamento": 5, "dia_vencimento": 12},
    )

    cat_salario = get_ou_criar(headers, "/categorias", "Salário (seed)", {"tipo": "receita"})
    cat_moradia = get_ou_criar(headers, "/categorias", "Moradia (seed)", {"tipo": "despesa"})
    cat_mercado = get_ou_criar(headers, "/categorias", "Mercado (seed)", {"tipo": "despesa"})
    cat_lazer = get_ou_criar(headers, "/categorias", "Lazer (seed)", {"tipo": "despesa"})
    cat_invest = get_ou_criar(headers, "/categorias", "Renda Fixa (seed)", {"tipo": "investimento"})

    sub_aluguel = get_ou_criar(
        headers, "/subcategorias", "Aluguel (seed)",
        {"categoria_id": cat_moradia["id"], "estrutura_custo_padrao": "fixo"},
    )
    sub_supermercado = get_ou_criar(
        headers, "/subcategorias", "Supermercado (seed)",
        {"categoria_id": cat_mercado["id"], "estrutura_custo_padrao": "variavel"},
    )

    caixinha = get_ou_criar(headers, "/caixinhas", "Reserva de Emergência (seed)")

    hoje = date.today()
    criados = 0

    for meses_atras in range(3, -1, -1):  # últimos 3 meses + o atual
        ano, mes = mes_offset(hoje, meses_atras)
        # orçamento sempre antes dos lançamentos do mês: assim os itens de
        # Aluguel/Mercado/Investimento já existem quando a transação chega,
        # e a sincronização reativa (sincronizar_item_orcamento) não cria
        # item duplicado a R$0 no lugar do item com valor de verdade.
        garantir_orcamento_mes(headers, ano, mes, sub_aluguel, sub_supermercado, cat_invest)

        def d(dia: int, ano=ano, mes=mes) -> str:
            return date(ano, mes, min(dia, 28)).isoformat()

        lancamentos = [
            ("/transacoes", {
                "data_compra": d(5), "valor": 5200, "descricao": f"{PREFIXO} Salário",
                "tipo_movimento": "receita", "conta_id": corrente["id"], "categoria_id": cat_salario["id"],
            }),
            ("/transacoes", {
                "data_compra": d(10), "valor": 1500, "descricao": f"{PREFIXO} Aluguel",
                "tipo_movimento": "despesa", "conta_id": corrente["id"], "categoria_id": cat_moradia["id"],
                "subcategoria_id": sub_aluguel["id"], "estrutura_custo": "fixo",
                "meio_pagamento": "debito_automatico",
            }),
            ("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(80, 250), 2),
                "descricao": f"{PREFIXO} Lazer", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat_lazer["id"], "estrutura_custo": "variavel", "meio_pagamento": "cartao_credito",
            }),
            ("/transacoes", {
                "data_compra": d(15), "valor": 500, "descricao": f"{PREFIXO} Aporte mensal",
                "tipo_movimento": "aplicacao", "conta_id": corrente["id"], "categoria_id": cat_invest["id"],
                "estrutura_custo": "investimentos",
            }),
            ("/transacoes", {
                "data_compra": d(15), "valor": 300, "descricao": f"{PREFIXO} Reserva mensal",
                "tipo_movimento": "aplicacao", "conta_id": corrente["id"], "caixinha_id": caixinha["id"],
            }),
        ]
        for _ in range(4):
            lancamentos.append(("/transacoes", {
                "data_compra": d(random.randint(1, 27)), "valor": round(random.uniform(60, 320), 2),
                "descricao": f"{PREFIXO} Supermercado", "tipo_movimento": "despesa", "conta_id": cartao["id"],
                "categoria_id": cat_mercado["id"], "subcategoria_id": sub_supermercado["id"],
                "estrutura_custo": "variavel", "meio_pagamento": "cartao_credito",
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
            "conta_id": cartao["id"], "categoria_id": cat_lazer["id"], "estrutura_custo": "variavel",
            "meio_pagamento": "cartao_credito",
        },
        headers=headers,
    )
    if resposta.status_code == 201:
        criados += len(resposta.json())

    print(f"{criados} lançamento(s) criado(s) com prefixo \"{PREFIXO}\".")


def limpar(headers: dict) -> None:
    todas = client.get("/transacoes", headers=headers).json()
    alvo = [t for t in todas if (t.get("descricao") or "").startswith(PREFIXO)]
    for t in alvo:
        client.delete(f"/transacoes/{t['id']}", headers=headers)
    print(f"{len(alvo)} lançamento(s) de seed removido(s).")


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
