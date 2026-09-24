from typing import Any

from fastapi import HTTPException
from supabase import Client


class NotFound(LookupError):
    """Registro não existe ou não pertence ao usuário autenticado."""


def list_all(db: Client, table: str, user_id: str, order: str = "nome") -> list[dict[str, Any]]:
    result = db.table(table).select("*").eq("user_id", user_id).order(order).execute()
    return result.data


def get_one(db: Client, table: str, user_id: str, item_id: str) -> dict[str, Any]:
    result = db.table(table).select("*").eq("id", item_id).eq("user_id", user_id).execute()
    if not result.data:
        raise NotFound(item_id)
    return result.data[0]


def create(db: Client, table: str, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Cria a linha; traduz violação de UNIQUE (categorias/subcategorias/
    caixinhas têm `unique(user_id, nome)` ou `unique(categoria_id, nome)`
    no schema) em 409 em vez de deixar a exceção crua do Postgrest
    subir — sem isso, criar um nome duplicado quebrava com um 500/erro
    não tratado em vez de uma resposta que o frontend já sabe exibir
    (mesmo padrão que orcamentos._insert_orcamento já usava)."""
    row = {**payload, "user_id": user_id}
    try:
        result = db.table(table).insert(row).execute()
    except Exception as exc:  # noqa: BLE001 — traduzimos a violação conhecida; o resto sobe
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(status_code=409, detail="Já existe um registro com esse nome.") from exc
        raise
    return result.data[0]


def update(db: Client, table: str, user_id: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = db.table(table).update(payload).eq("id", item_id).eq("user_id", user_id).execute()
    if not result.data:
        raise NotFound(item_id)
    return result.data[0]


def set_ativo(db: Client, table: str, user_id: str, item_id: str, ativo: bool) -> dict[str, Any]:
    return update(db, table, user_id, item_id, {"ativo": ativo})


def get_owned(db: Client, table: str, user_id: str, item_id: str) -> dict[str, Any] | None:
    """Confere que um registro referenciado (ex: categoria_id de uma
    subcategoria) realmente pertence ao usuário antes de vincular — o
    RLS não impede um FK apontar para registro de outro usuário."""
    result = db.table(table).select("id").eq("id", item_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None
