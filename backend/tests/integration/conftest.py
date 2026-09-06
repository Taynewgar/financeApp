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


@pytest.fixture
def cleanup():
    """Registre (tabela, id) durante o teste; tudo é apagado ao final,
    mesmo se o teste falhar no meio. Ordem de apagar é a inversa da
    ordem de criação (LIFO), então dependências saem antes dos pais."""
    created: list[tuple[str, str]] = []
    yield created
    admin = get_service_client()
    for table, item_id in reversed(created):
        try:
            admin.table(table).delete().eq("id", item_id).execute()
        except Exception:
            pass
