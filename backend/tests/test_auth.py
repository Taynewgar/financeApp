import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PROTECTED_GET_ENDPOINTS = ["/contas", "/categorias", "/subcategorias", "/caixinhas", "/transacoes"]


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
def test_requires_authorization_header(path):
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", PROTECTED_GET_ENDPOINTS)
def test_rejects_malformed_authorization_header(path):
    response = client.get(path, headers={"Authorization": "Basic algumacoisa"})
    assert response.status_code == 401
