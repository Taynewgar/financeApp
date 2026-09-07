import httpx
import jwt
from fastapi import Depends, Header, HTTPException
from supabase import Client

from .config import settings
from .db import get_user_client


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")
    return authorization.removeprefix("Bearer ").strip()


def _validar_localmente(token: str) -> str:
    """Verifica a assinatura HS256 do token com o JWT Secret do projeto —
    sem chamada de rede. É o mesmo token que o Supabase Auth emitiu, só
    verificado no processo local em vez de perguntar pro Supabase."""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        print(f"[auth] token rejeitado na validação local: {exc!r}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado") from exc
    return payload["sub"]


def _validar_remoto(token: str) -> str:
    # Chamada direta ao endpoint do Supabase (em vez de passar pelo SDK) para
    # que uma falha real apareça no log do servidor, não vire um "token
    # inválido" genérico que esconde a causa de verdade. Custa uma
    # requisição de rede extra por chamada — use SUPABASE_JWT_SECRET pra
    # evitar isso (ver _validar_localmente).
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


def get_current_user_id(token: str = Depends(get_token)) -> str:
    if settings.supabase_jwt_secret:
        return _validar_localmente(token)
    return _validar_remoto(token)


def get_db(token: str = Depends(get_token)) -> Client:
    return get_user_client(token)
