"""Fixtures dos testes de integração — estes tocam o Supabase de verdade.

Diferente dos testes em tests/ (que usam FakeSupabaseClient e rodam em
qualquer lugar, sem rede), estes validam o que o dublê não pode provar:
que o RLS do Postgres realmente isola os dados entre usuários, e que a
constraint UNIQUE de hash_dedup existe de verdade no banco.

Pulados automaticamente se o ambiente não tiver .env configurado e
TEST_USER_EMAIL/TEST_USER_PASSWORD definidos — não quebram CI nem rodam
por engano num ambiente sem rede.
"""
from __future__ import annotations

import os
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import get_service_client
from app.main import app

_TEST_EMAIL = os.environ.get("TEST_USER_EMAIL")
_TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD")

_CONFIGURADO = bool(_TEST_EMAIL and _TEST_PASSWORD and settings.supabase_url and settings.supabase_anon_key)


@pytest.fixture(autouse=True)
def _pula_sem_supabase_real():
    """pytestmark em conftest.py não alcança testes de outros arquivos —
    por isso o pulo é uma fixture autouse, que roda antes de qualquer
    outra fixture do teste (inclusive headers_a/headers_b)."""
    if not _CONFIGURADO:
        pytest.skip(
            "Testes de integração exigem backend/.env preenchido e as variáveis "
            "TEST_USER_EMAIL/TEST_USER_PASSWORD (um usuário já criado no Supabase). "
            "Veja backend/.env.example."
        )


def _sign_in(email: str, password: str) -> str:
    resp = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def real_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def headers_a() -> dict[str, str]:
    token = _sign_in(_TEST_EMAIL, _TEST_PASSWORD)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def headers_b():
    """Usuário descartável, criado e apagado só para este teste — usado
    para provar isolamento (RLS) contra o usuário principal."""
    admin = get_service_client()
    email = f"pytest-{uuid.uuid4().hex[:10]}@teste.local"
    password = "pytest-temporaria-123"
    created = admin.auth.admin.create_user({"email": email, "password": password, "email_confirm": True})
    token = _sign_in(email, password)
    yield {"Authorization": f"Bearer {token}"}
    admin.auth.admin.delete_user(created.user.id)


# ordem segura de FK pra apagar — mesma lógica de
# tests/limpar_dados_integracao.py: transacoes/orcamento_itens referenciam
# categorias/subcategorias/contas/caixinhas sem "on delete cascade", então
# têm que sumir antes dos "pais". orcamento_itens cascade a partir de
# orcamentos, mas apagar explícito aqui não atrapalha e cobre o caso de um
# teste que cria o item sem apagar o orçamento-pai. Tabela fora desta lista
# (não deveria acontecer) cai no fim, ordenada por nome, só pra não quebrar.
_ORDEM_SEGURA = {
    "orcamento_itens": 0,
    "transacoes": 1,
    "orcamentos": 2,
    "caixinhas": 3,
    "compras_parceladas": 4,
    "subcategorias": 5,
    "categorias": 6,
    "contas": 7,
}


@pytest.fixture
def cleanup():
    """Registre (tabela, id) durante o teste; tudo é apagado ao final,
    mesmo se o teste falhar no meio.

    A ordem de apagar NÃO é a reversa da ordem de criação (LIFO) — testes
    costumam criar o orçamento antes da categoria e só depois o item que
    referencia os dois, então LIFO tentava apagar a categoria antes do
    orçamento (e do item que ainda a referenciava), a FK bloqueava, o erro
    era engolido e a categoria ficava presa pra sempre (é o que gerava o
    "duplicate key" e o orçamento fantasma em rodadas seguintes). A ordem
    aqui é fixa e respeita as FKs de verdade, igual
    tests/limpar_dados_integracao.py, não importa em que ordem o teste
    chamou cleanup.append."""
    created: list[tuple[str, str]] = []
    yield created
    admin = get_service_client()
    # ajuste_de_transacao_id é auto-referente (estorno aponta pra despesa
    # original) sem cascade — zera antes de apagar, mesma defesa de
    # limpar_dados_integracao.py, pro caso de um teste futuro rastrear as
    # duas transações e a ordem entre elas não ser a que a FK exige.
    for table, item_id in created:
        if table == "transacoes":
            try:
                admin.table("transacoes").update({"ajuste_de_transacao_id": None}).eq("id", item_id).execute()
            except Exception:
                pass
    for table, item_id in sorted(created, key=lambda par: _ORDEM_SEGURA.get(par[0], 99)):
        try:
            admin.table(table).delete().eq("id", item_id).execute()
        except Exception as exc:
            # não propaga (não pode quebrar o teste na limpeza), mas avisa
            # no output — antes isso era engolido em silêncio e o dado
            # ficava preso sem ninguém perceber até esbarrar num unique
            # constraint numa rodada futura
            print(f"[cleanup] falha ao apagar {table}/{item_id}: {exc!r}")
