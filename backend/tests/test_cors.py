from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_origem_do_frontend_local_recebe_cabecalho_cors():
    """Sem isso, o navegador bloqueia silenciosamente toda chamada do
    frontend (Vite, em localhost:5173 por padrão) pro backend — é o que
    fazia o Dashboard mostrar "indisponível" mesmo com o backend no ar."""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_origem_desconhecida_nao_recebe_cabecalho_cors():
    response = client.get("/health", headers={"Origin": "https://site-nao-autorizado.com"})
    assert "access-control-allow-origin" not in response.headers
