"""Dublê do cliente Supabase para testes offline.

Reproduz só o encadeamento usado pelo código real
(.table().select()/.insert()/.update()/.delete().eq()...order().execute())
sobre um dicionário em memória — sem rede, sem Supabase real. Isso testa a
lógica da nossa API (validação, cálculo de fatura, hash_dedup, checagem de
posse entre recursos) de verdade, mas não substitui a checagem de RLS do
Postgres em si — essa continua sendo o papel do manual_verification.py
contra o banco real.
"""
from __future__ import annotations

import uuid
from typing import Any


class FakeResult:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


# espelha constraints UNIQUE(...) compostas do schema.sql que não são
# cobertas pelo caso genérico de hash_dedup (ex: orcamentos(user_id, vigencia_mes))
_UNIQUE_CONSTRAINTS: dict[str, tuple[str, ...]] = {
    "orcamentos": ("user_id", "vigencia_mes"),
    "lancamentos_recorrentes_pulados": ("lancamento_recorrente_id", "vigencia_mes"),
}


class FakeQuery:
    def __init__(self, rows: list[dict[str, Any]], table: str = ""):
        self._rows = rows
        self._table = table
        self._filters: list[tuple[str, str, Any]] = []
        self._order_key: str | None = None
        self._order_desc = False
        self._op: str | None = None
        self._payload: dict[str, Any] | None = None

    def select(self, _columns: str = "*") -> "FakeQuery":
        self._op = "select"
        return self

    def insert(self, payload: dict[str, Any]) -> "FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        return self

    def update(self, payload: dict[str, Any]) -> "FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        return self

    def delete(self) -> "FakeQuery":
        self._op = "delete"
        return self

    def eq(self, key: str, value: Any) -> "FakeQuery":
        self._filters.append(("eq", key, value))
        return self

    def gte(self, key: str, value: Any) -> "FakeQuery":
        self._filters.append(("gte", key, value))
        return self

    def gt(self, key: str, value: Any) -> "FakeQuery":
        self._filters.append(("gt", key, value))
        return self

    def lt(self, key: str, value: Any) -> "FakeQuery":
        self._filters.append(("lt", key, value))
        return self

    def lte(self, key: str, value: Any) -> "FakeQuery":
        self._filters.append(("lte", key, value))
        return self

    def ilike(self, key: str, pattern: str) -> "FakeQuery":
        # só cobre o uso real do código: sempre "%termo%" (contains, case-insensitive)
        self._filters.append(("ilike", key, pattern.strip("%").lower()))
        return self

    def is_(self, key: str, value: Any) -> "FakeQuery":
        # só cobre o uso real do código: checagem de IS NULL
        self._filters.append(("is", key, value))
        return self

    def in_(self, key: str, values: list[Any]) -> "FakeQuery":
        self._filters.append(("in", key, values))
        return self

    def order(self, key: str, desc: bool = False) -> "FakeQuery":
        self._order_key = key
        self._order_desc = desc
        return self

    def _matches(self, row: dict[str, Any]) -> bool:
        for op, key, value in self._filters:
            atual = row.get(key)
            if op == "eq" and atual != value:
                return False
            if op == "gte" and not (atual is not None and atual >= value):
                return False
            if op == "gt" and not (atual is not None and atual > value):
                return False
            if op == "lt" and not (atual is not None and atual < value):
                return False
            if op == "lte" and not (atual is not None and atual <= value):
                return False
            if op == "ilike" and value not in (atual or "").lower():
                return False
            if op == "is" and atual is not None:
                return False
            if op == "in" and atual not in value:
                return False
        return True

    def execute(self) -> FakeResult:
        if self._op == "select":
            matched = [dict(r) for r in self._rows if self._matches(r)]
            if self._order_key:
                matched.sort(key=lambda r: r.get(self._order_key), reverse=self._order_desc)
            return FakeResult(matched)

        if self._op == "insert":
            row = dict(self._payload or {})
            row.setdefault("id", str(uuid.uuid4()))
            # espelha os defaults de coluna do schema.sql (Postgres preenche
            # isso sozinho; o app nunca envia "ativo" na criação)
            row.setdefault("ativo", True)
            if self._table == "orcamento_itens":
                row.setdefault("saldo_anterior", 0)
            if "hash_dedup" in row:
                for existing in self._rows:
                    if existing.get("hash_dedup") == row["hash_dedup"]:
                        raise Exception(
                            "duplicate key value violates unique constraint \"transacoes_hash_dedup_key\""
                        )
            colunas_unicas = _UNIQUE_CONSTRAINTS.get(self._table)
            if colunas_unicas:
                chave = tuple(row.get(c) for c in colunas_unicas)
                for existing in self._rows:
                    if tuple(existing.get(c) for c in colunas_unicas) == chave:
                        raise Exception(
                            f"duplicate key value violates unique constraint \"{self._table}_{'_'.join(colunas_unicas)}_key\""
                        )
            self._rows.append(row)
            return FakeResult([dict(row)])

        if self._op == "update":
            matched = [r for r in self._rows if self._matches(r)]
            for r in matched:
                r.update(self._payload or {})
            return FakeResult([dict(r) for r in matched])

        if self._op == "delete":
            matched = [r for r in self._rows if self._matches(r)]
            for r in matched:
                self._rows.remove(r)
            return FakeResult([dict(r) for r in matched])

        raise RuntimeError("nenhuma operação (select/insert/update/delete) foi chamada antes de execute()")


class FakeSupabaseClient:
    """Substitui supabase.Client nos testes. `store` é compartilhado entre
    chamadas dentro de um mesmo teste para simular um banco persistente."""

    def __init__(self, store: dict[str, list[dict[str, Any]]]):
        self._store = store

    def table(self, name: str) -> FakeQuery:
        self._store.setdefault(name, [])
        return FakeQuery(self._store[name], table=name)
