import httpx
from fastapi import Depends, Header, HTTPException
from supabase import Client

from .config import settings
from .db import get_user_client


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")
    return authorization.removeprefix("Bearer ").strip()


def get_current_user_id(token: str = Depends(get_token)) -> str:
    # Chamada direta ao endpoint do Supabase (em vez de passar pelo SDK) para
    # que uma falha real apareça no log do servidor, não vire um "token
    # inválido" genérico que esconde a causa de verdade.
    try:
        response = httpx.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        print(f"[auth] falha de rede ao validar token: {exc!r}")
        raise HTTPException(status_code=401, detail="Não foi possível validar o token") from exc

    if response.status_code != 200:
        print(f"[auth] token rejeitado pelo Supabase: status={response.status_code} body={response.text}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return response.json()["id"]


def get_db(token: str = Depends(get_token)) -> Client:
    return get_user_client(token)
