from typing import Any

from supabase import Client


class NotFound(LookupError):
    """Registro não existe ou não pertence ao usuário autenticado."""


def list_all(db: Client, table: str, user_id: str, order: str = "nome") -> list[dict[str, Any]]:
    result = db.table(table).select("*").eq("user_id", user_id).order(order).execute()
    return result.data


def create(db: Client, table: str, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {**payload, "user_id": user_id}
    result = db.table(table).insert(row).execute()
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
