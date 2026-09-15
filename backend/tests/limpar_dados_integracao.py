"""Reseta os dados da conta de teste dedicada usada pelos testes de
integração (mesma conta de TEST_USER_EMAIL/TEST_USER_PASSWORD) — apaga tudo
que essa conta tem em transações/orçamentos/caixinhas/compras parceladas/
categorias/contas, direto no banco (bypassa RLS via service_role, faz
DELETE de verdade — a API só desativa, nunca exclui de fato).

Por que existe: os testes de integração (tests/integration/) criam
categorias/orçamentos com nomes e meses de vigência fixos (ex: "Categoria
Integração", vigência 2026-09-01). Se uma rodada anterior for interrompida
no meio (Ctrl+C, timeout de rede) antes da fixture `cleanup` terminar, esses
registros ficam presos e bloqueiam toda rodada seguinte (unique constraint
de nome de categoria, ou de orçamento por mês). Rode este script pra
"zerar" a conta de teste e destravar.

Seguro: só mexe em dados do usuário TEST_USER_EMAIL, filtrando
explicitamente por esse user_id — nunca no seu usuário pessoal (RLS já
separa os dois por padrão; esta filtragem é redundante de propósito).
Pede confirmação antes de apagar, mostrando quantas linhas existem em cada
tabela. Roda contra o Supabase de verdade (mesmo projeto dos testes de
integração e do seed) — não é ambiente de CI.

Uso:
    cd backend
    source venv/bin/activate
    TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste \
        python tests/limpar_dados_integracao.py

    # pra pular a confirmação interativa:
    TEST_USER_EMAIL=teste@teste.com TEST_USER_PASSWORD=teste \
        python tests/limpar_dados_integracao.py --sim
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys

import httpx

sys.path.insert(0, ".")
from app.config import settings  # noqa: E402
from app.db import get_service_client  # noqa: E402

# Ordem que respeita as foreign keys sem cascade automático (transacoes e
# orcamento_itens referenciam categorias/subcategorias/contas/caixinhas sem
# "on delete cascade"; orcamento_itens em si cascade a partir de orcamentos,
# então não precisa de tabela própria aqui). Apagar nesta ordem garante que
# nada referenciado ainda existe quando a tabela "pai" é apagada depois.
TABELAS_NA_ORDEM = [
    "transacoes",
    "orcamentos",
    "caixinhas",
    "compras_parceladas",
    "categorias",
    "contas",
]


def sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def user_id_do_token(access_token: str) -> str:
    """Extrai o 'sub' (user id) do JWT sem verificar assinatura — só
    leitura local; o sign-in acima já provou que o token é válido (foi o
    próprio Supabase que emitiu)."""
    payload_b64 = access_token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)  # completa o padding do base64url
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    return payload["sub"]


def contar(admin, user_id: str) -> dict[str, int]:
    return {
        tabela: len(admin.table(tabela).select("id").eq("user_id", user_id).execute().data)
        for tabela in TABELAS_NA_ORDEM
    }


def limpar(admin, user_id: str) -> None:
    # ajuste_de_transacao_id é auto-referente (uma transação aponta pra
    # outra) — zera antes de apagar em massa pra não esbarrar na FK.
    admin.table("transacoes").update({"ajuste_de_transacao_id": None}).eq("user_id", user_id).execute()
    for tabela in TABELAS_NA_ORDEM:
        admin.table(tabela).delete().eq("user_id", user_id).execute()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sim", action="store_true", help="pula a confirmação interativa")
    args = parser.parse_args()

    email = os.environ.get("TEST_USER_EMAIL")
    password = os.environ.get("TEST_USER_PASSWORD")
    if not email or not password or not settings.supabase_url:
        sys.exit("Defina TEST_USER_EMAIL/TEST_USER_PASSWORD e backend/.env (mesmo usuário dos testes de integração).")

    user_id = user_id_do_token(sign_in(email, password))
    admin = get_service_client()

    contagens = contar(admin, user_id)
    total = sum(contagens.values())
    if total == 0:
        print(f"Conta {email} já está limpa (0 registros).")
        return

    print(f"Conta {email} (user_id={user_id}) tem:")
    for tabela, n in contagens.items():
        if n:
            print(f"  {n:>4}  {tabela}")

    if not args.sim:
        resposta = input("\nApagar tudo isso? Essa conta é dedicada a testes — nunca mexe no seu usuário pessoal. [s/N] ")
        if resposta.strip().lower() != "s":
            print("Cancelado.")
            return

    limpar(admin, user_id)
    print("Pronto — conta de teste zerada.")


if __name__ == "__main__":
    main()
