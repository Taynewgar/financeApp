"""Popula o Supabase real de um usuário com lançamentos variados, pra testar
telas (Lançamentos, Dashboard, Estrutura de Custo) com dados mais coerentes
do que uns poucos lançamentos manuais soltos.

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
