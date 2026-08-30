from fastapi import FastAPI

from .config import settings
from .routers import caixinhas, categorias, contas, subcategorias

app = FastAPI(title="Finance App API")

app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(subcategorias.router)
app.include_router(caixinhas.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_configured": bool(
            settings.supabase_url and settings.supabase_anon_key and settings.supabase_service_role_key
        ),
    }
