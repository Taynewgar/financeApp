from supabase import Client, create_client

from .config import settings


def get_service_client() -> Client:
    """Cliente com service_role — só para tarefas administrativas (validar
    token, migração). Ignora RLS por completo; nunca usar para ler/escrever
    dados de um usuário específico."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_user_client(access_token: str) -> Client:
    """Cliente autenticado como o usuário dono do token — RLS é aplicado
    normalmente pelo Postgres, então isolamento por usuário é garantido no
    banco, não só no código da API."""
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
