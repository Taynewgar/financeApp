import httpx
import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient
from supabase import Client

from .config import settings
from .db import get_user_client


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou mal formatado")
    return authorization.removeprefix("Bearer ").strip()


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json", cache_keys=True)
    return _jwks_client


def _validar_localmente(token: str) -> str | None:
    """Verifica a assinatura do token com a chave pública do projeto (JWKS)
    — sem segredo compartilhado nenhum pra configurar, e sem chamada de
    rede a cada request (a chave pública fica em cache local, só é
    buscada de novo se o Supabase rotacionar as chaves). Só funciona se o
    projeto usa chaves de assinatura assimétricas (ES256/RS256 — o padrão
    atual do Supabase); projetos ainda no segredo HS256 legado (que o
    Supabase está descontinuando) não têm chave pública pra publicar, daí
    retorna None e quem chamou cai pro validador remoto."""
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    except jwt.PyJWKClientError:
        return None
    try:
        payload = jwt.decode(token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated")
    except jwt.PyJWTError as exc:
        print(f"[auth] token rejeitado na validação local: {exc!r}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado") from exc
    return payload["sub"]


def _validar_remoto(token: str) -> str:
    # Chamada direta ao endpoint do Supabase (em vez de passar pelo SDK) para
    # que uma falha real apareça no log do servidor, não vire um "token
    # inválido" genérico que esconde a causa de verdade. Custa uma
    # requisição de rede extra por chamada — só é usado quando o projeto
    # não expõe chave pública via JWKS (ver _validar_localmente).
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
    if settings.supabase_url:
        user_id = _validar_localmente(token)
        if user_id is not None:
            return user_id
    return _validar_remoto(token)


def get_db(token: str = Depends(get_token)) -> Client:
    return get_user_client(token)
