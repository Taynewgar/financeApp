from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração via variáveis de ambiente.

    Tudo é opcional aqui de propósito: o serviço precisa subir e responder
    /health mesmo antes de o Supabase estar conectado (Entrega 1).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    database_url: str | None = None


settings = Settings()
