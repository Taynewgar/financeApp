from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração via variáveis de ambiente.

    Tudo é opcional aqui de propósito: o serviço precisa subir e responder
    /health mesmo antes de o Supabase estar conectado (Entrega 1).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    database_url: str | None = None
    # origens do frontend com permissão de CORS, separadas por vírgula —
    # já vem com as portas padrão do Vite pra funcionar em dev local sem
    # precisar configurar nada; em produção, defina com a URL publicada
    # do frontend (Render/Vercel/etc)
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def frontend_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


settings = Settings()
