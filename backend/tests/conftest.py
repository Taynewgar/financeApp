import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user_id, get_db
from app.main import app

from .fakes import FakeSupabaseClient


@pytest.fixture
def db_store():
    """Um "banco" em memória por teste — nunca compartilhado entre testes."""
    return {}


@pytest.fixture
def current_user():
    """Dict mutável: mude current_user['id'] no meio do teste pra simular
    uma segunda pessoa fazendo a próxima requisição (testes de posse)."""
    return {"id": "11111111-1111-1111-1111-111111111111"}


@pytest.fixture
def client(db_store, current_user):
    app.dependency_overrides[get_db] = lambda: FakeSupabaseClient(db_store)
    app.dependency_overrides[get_current_user_id] = lambda: current_user["id"]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


OUTRO_USUARIO = "22222222-2222-2222-2222-222222222222"
