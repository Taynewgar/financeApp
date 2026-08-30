from fastapi import Depends, Header, HTTPException
from supabase import Client

from .db import get_service_client, get_user_client


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")
    return authorization.removeprefix("Bearer ").strip()


def get_current_user_id(token: str = Depends(get_token)) -> str:
    try:
        result = get_service_client().auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    if not result or not result.user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return result.user.id


def get_db(token: str = Depends(get_token)) -> Client:
    return get_user_client(token)
