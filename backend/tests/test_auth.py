import jwt
import pytest
from fastapi.testclient import TestClient

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


class TestValidacaoLocalDeToken:
    """SUPABASE_JWT_SECRET setado -> valida a assinatura localmente, sem
    chamar o Supabase — evita a requisição de rede extra em toda chamada."""

    def setup_method(self):
        settings.supabase_jwt_secret = "segredo-de-teste"
        app.dependency_overrides[get_db] = lambda: FakeSupabaseClient({"contas": []})

    def teardown_method(self):
        settings.supabase_jwt_secret = None
        app.dependency_overrides.clear()

    def _token(self, **overrides):
        payload = {"sub": "11111111-1111-1111-1111-111111111111", "aud": "authenticated", **overrides}
        return jwt.encode(payload, "segredo-de-teste", algorithm="HS256")

    def test_token_assinado_corretamente_e_aceito(self):
        resposta = client.get("/contas", headers={"Authorization": f"Bearer {self._token()}"})
        assert resposta.status_code == 200

    def test_token_com_assinatura_invalida_retorna_401(self):
        token_forjado = jwt.encode(
            {"sub": "11111111-1111-1111-1111-111111111111", "aud": "authenticated"},
            "segredo-errado",
            algorithm="HS256",
        )
        resposta = client.get("/contas", headers={"Authorization": f"Bearer {token_forjado}"})
        assert resposta.status_code == 401

    def test_token_com_audience_errada_retorna_401(self):
        token = self._token(aud="outra-coisa")
        resposta = client.get("/contas", headers={"Authorization": f"Bearer {token}"})
        assert resposta.status_code == 401
