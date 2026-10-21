from typing import Any, Callable

from fastapi import HTTPException
from supabase import Client


class NotFound(LookupError):
    """Registro não existe ou não pertence ao usuário autenticado."""


def buscar_todas_paginado(construir_query: Callable[[], Any], tamanho_pagina: int = 1000) -> list[dict[str, Any]]:
    """O Supabase (PostgREST) limita a resposta a `tamanho_pagina` linhas
    quando a query não pede uma página explícita (`db-max-rows`, 1000 por
    padrão nos projetos hospedados) — sem erro nenhum, só devolve menos
    do que existe, e sem `.order()` nem garante QUAIS linhas. Passou
    despercebido enquanto os dados eram poucos (seed/teste); virou bug de
    cálculo real assim que uma conta de uso real passou de 1000
    transações (achado em 2026-09-25, ver docs/backlog.md — a tela de
    Caixinhas ficava com saldo errado, silenciosamente, pra caixinhas
    cujas transações caíam fora das 1000 primeiras linhas devolvidas).

    `construir_query` monta a query do zero a cada chamada, sem
    `.execute()` — o query builder do supabase-py não é reutilizável
    depois de executado, então não dá pra só guardar a query e paginar
    por cima dela."""
    linhas: list[dict[str, Any]] = []
    offset = 0
    while True:
        pagina = construir_query().range(offset, offset + tamanho_pagina - 1).execute().data
        linhas.extend(pagina)
        if len(pagina) < tamanho_pagina:
            return linhas
        offset += tamanho_pagina


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
