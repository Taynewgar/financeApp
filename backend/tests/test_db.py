from app.config import settings
from app.db import _httpx_compartilhado, get_service_client, get_user_client


def test_clientes_reaproveitam_a_mesma_conexao_httpx(monkeypatch):
    """Criar um httpx.Client novo por requisição paga o handshake TCP/TLS
    com o Supabase toda vez — é isso que deixava cada chamada da API
    visivelmente lenta. Trava aqui que os clientes continuam
    compartilhando a mesma conexão (get_db é chamado a cada request)."""
    monkeypatch.setattr(settings, "supabase_url", "https://exemplo-teste.supabase.co")
    monkeypatch.setattr(settings, "supabase_anon_key", "anon-fake")
    monkeypatch.setattr(settings, "supabase_service_role_key", "service-fake")

    cliente_a = get_user_client("token-a")
    cliente_b = get_user_client("token-b")
    cliente_servico = get_service_client()

    assert cliente_a.postgrest.session is _httpx_compartilhado
    assert cliente_b.postgrest.session is _httpx_compartilhado
    assert cliente_servico.postgrest.session is _httpx_compartilhado


def test_token_de_cada_cliente_fica_isolado(monkeypatch):
    """O token de autenticação não pode vazar entre requisições concorrentes
    de usuários diferentes — cada get_user_client() precisa carregar o seu
    próprio, mesmo compartilhando a conexão TCP/TLS."""
    monkeypatch.setattr(settings, "supabase_url", "https://exemplo-teste.supabase.co")
    monkeypatch.setattr(settings, "supabase_anon_key", "anon-fake")

    cliente_a = get_user_client("token-a")
    cliente_b = get_user_client("token-b")

    assert cliente_a.postgrest.headers["Authorization"] == "Bearer token-a"
    assert cliente_b.postgrest.headers["Authorization"] == "Bearer token-b"
