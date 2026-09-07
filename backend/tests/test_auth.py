import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app import auth
from app.auth import get_db
from app.config import settings
from app.main import app

from .fakes import FakeSupabaseClient

client = TestClient(app)

PROTECTED_GET_ENDPOINTS = [
    "/contas",
    "/contas/00000000-0000-0000-0000-000000000000",
    "/categorias",
    "/categorias/00000000-0000-0000-0000-000000000000",
    "/subcategorias",
    "/subcategorias/00000000-0000-0000-0000-000000000000",
    "/caixinhas",
    "/caixinhas/00000000-0000-0000-0000-000000000000",
    "/transacoes",
    "/transacoes/00000000-0000-0000-0000-000000000000",
]


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
def test_requires_authorization_header(path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
def test_rejects_malformed_authorization_header(path):
    response = client.get(path, headers={"Authorization": "Basic algumacoisa"})
    assert response.status_code == 401


class _SigningKeyStub:
    def __init__(self, key):
        self.key = key


class _JwksClientStub:
    """Fica no lugar de PyJWKClient nos testes — devolve a chave pública
    fixa em vez de buscar de um endpoint JWKS de verdade."""

    def __init__(self, chave_publica):
        self._chave_publica = chave_publica

    def get_signing_key_from_jwt(self, token):
        return _SigningKeyStub(self._chave_publica)


@pytest.fixture
def jwks_local(monkeypatch):
    """Simula um projeto com chaves de assinatura assimétricas (ES256) —
    o caminho local via JWKS, sem segredo compartilhado nenhum."""
    chave_privada = ec.generate_private_key(ec.SECP256R1())
    chave_publica = chave_privada.public_key()

    monkeypatch.setattr(settings, "supabase_url", "https://exemplo-teste.supabase.co")
    monkeypatch.setattr(auth, "_get_jwks_client", lambda: _JwksClientStub(chave_publica))
    app.dependency_overrides[get_db] = lambda: FakeSupabaseClient({"contas": []})

    def _token(**overrides):
        payload = {"sub": "11111111-1111-1111-1111-111111111111", "aud": "authenticated", **overrides}
        return jwt.encode(payload, chave_privada, algorithm="ES256")

    yield _token

    app.dependency_overrides.clear()


def test_token_assinado_com_a_chave_publica_correta_e_aceito(jwks_local):
    resposta = client.get("/contas", headers={"Authorization": f"Bearer {jwks_local()}"})
    assert resposta.status_code == 200


def test_token_assinado_com_outra_chave_retorna_401(jwks_local):
    outra_chave = ec.generate_private_key(ec.SECP256R1())
    token_forjado = jwt.encode(
        {"sub": "11111111-1111-1111-1111-111111111111", "aud": "authenticated"},
        outra_chave,
        algorithm="ES256",
    )
    resposta = client.get("/contas", headers={"Authorization": f"Bearer {token_forjado}"})
    assert resposta.status_code == 401


def test_token_com_audience_errada_retorna_401(jwks_local):
    resposta = client.get("/contas", headers={"Authorization": f"Bearer {jwks_local(aud='outra-coisa')}"})
    assert resposta.status_code == 401


def test_sem_chave_publica_disponivel_cai_pro_validador_remoto(monkeypatch):
    """Projeto ainda no segredo HS256 legado (sem JWKS) — não deve quebrar,
    só cair pro validador remoto (aqui simulado como indisponível, só pra
    confirmar que o fallback é acionado em vez de um erro não tratado)."""
    monkeypatch.setattr(settings, "supabase_url", "https://exemplo-teste.supabase.co")
    monkeypatch.setattr(
        auth,
        "_get_jwks_client",
        lambda: (_ for _ in ()).throw(jwt.PyJWKClientError("sem JWKS")),
    )

    def _remoto_indisponivel(*args, **kwargs):
        raise auth.httpx.ConnectError("sem rede no teste")

    monkeypatch.setattr(auth.httpx, "get", _remoto_indisponivel)
    app.dependency_overrides[get_db] = lambda: FakeSupabaseClient({"contas": []})
    try:
        resposta = client.get("/contas", headers={"Authorization": "Bearer token-qualquer"})
    finally:
        app.dependency_overrides.clear()
    assert resposta.status_code == 401
