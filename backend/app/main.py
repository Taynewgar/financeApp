from fastapi import FastAPI

from .config import settings

app = FastAPI(title="Finance App API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role_key),
    }
