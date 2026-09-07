from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import caixinhas, categorias, contas, dashboard, estrutura_custo, orcamentos, subcategorias, transacoes

app = FastAPI(title="Finance App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(subcategorias.router)
app.include_router(caixinhas.router)
app.include_router(transacoes.router)
app.include_router(orcamentos.router)
app.include_router(estrutura_custo.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_configured": bool(
            settings.supabase_url and settings.supabase_anon_key and settings.supabase_service_role_key
        ),
    }
