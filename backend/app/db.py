import httpx
from supabase import Client, ClientOptions, create_client

from .config import settings

# Reaproveitado entre requisições: criar um httpx.Client novo a cada
# chamada (o que create_client faz por padrão) paga a conexão TCP/TLS com
# o Supabase inteira toda vez — é o que estava deixando cada chamada da
# API visivelmente lenta (várias vezes por segundo, uma por request).
# httpx.Client é seguro pra compartilhar entre threads (é assim que o
# FastAPI roda endpoints síncronos), então isso não introduz race
# condition — o token de autenticação continua isolado por requisição,
# guardado num wrapper leve (o `Client` do Supabase) criado a cada
# chamada, nunca escrito nesse httpx.Client compartilhado.
_httpx_compartilhado = httpx.Client(timeout=30)
_opcoes_com_conexao_compartilhada = ClientOptions(httpx_client=_httpx_compartilhado)


def get_service_client() -> Client:
    """Cliente com service_role — só para tarefas administrativas (validar
    token, migração). Ignora RLS por completo; nunca usar para ler/escrever
    dados de um usuário específico."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=_opcoes_com_conexao_compartilhada,
    )


def get_user_client(access_token: str) -> Client:
    """Cliente autenticado como o usuário dono do token — RLS é aplicado
    normalmente pelo Postgres, então isolamento por usuário é garantido no
    banco, não só no código da API."""
    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=_opcoes_com_conexao_compartilhada,
    )
    client.postgrest.auth(access_token)
    return client
