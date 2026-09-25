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
from collections.abc import Callable
from typing import Any


class FakeResult:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


# espelha constraints UNIQUE(...) compostas do schema.sql que não são
# cobertas pelo caso genérico de hash_dedup (ex: orcamentos(user_id, vigencia_mes))
_UNIQUE_CONSTRAINTS: dict[str, tuple[str, ...]] = {
    "orcamentos": ("user_id", "vigencia_mes"),
    "lancamentos_recorrentes_pulados": ("lancamento_recorrente_id", "vigencia_mes"),
    "categorias": ("user_id", "nome"),
    "subcategorias": ("categoria_id", "nome"),
    "caixinhas": ("user_id", "nome"),
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
        self._range: tuple[int, int] | None = None

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

    def range(self, start: int, end: int) -> "FakeQuery":
        # mesma semântica do PostgREST: intervalo fechado, ambas as
        # pontas inclusive (.range(0, 999) = as primeiras 1000 linhas)
        self._range = (start, end)
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
            if self._range:
                start, end = self._range
                matched = matched[start : end + 1]
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


def _fake_saldo_caixinhas(transacoes: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    saldos: dict[str, float] = {}
    for t in transacoes:
        if t.get("user_id") != params["p_user_id"] or not t.get("caixinha_id"):
            continue
        if t["data_compra"] >= params["p_ate"]:
            continue
        sinal = 1 if t["tipo_movimento"] == "aplicacao" else -1
        saldos[t["caixinha_id"]] = saldos.get(t["caixinha_id"], 0.0) + sinal * t["valor"]
    return [{"caixinha_id": caixinha_id, "saldo": saldo} for caixinha_id, saldo in saldos.items()]


def _fake_resumo_agregado_transacoes(
    transacoes: list[dict[str, Any]], params: dict[str, Any]
) -> list[dict[str, Any]]:
    grupos: dict[tuple, float] = {}
    for t in transacoes:
        if t.get("user_id") != params["p_user_id"]:
            continue
        if not (params["p_desde"] <= t["data_compra"] < params["p_ate"]):
            continue
        chave = (t["tipo_movimento"], bool(t.get("ajuste_de_transacao_id")), bool(t.get("caixinha_id")))
        grupos[chave] = grupos.get(chave, 0.0) + t["valor"]
    return [
        {"tipo_movimento": tipo, "tem_ajuste": tem_ajuste, "tem_caixinha": tem_caixinha, "total": total}
        for (tipo, tem_ajuste, tem_caixinha), total in grupos.items()
    ]


def _fake_saldo_transacoes_agregado(
    transacoes: list[dict[str, Any]], params: dict[str, Any]
) -> list[dict[str, Any]]:
    grupos: dict[tuple, float] = {}
    for t in transacoes:
        if t.get("user_id") != params["p_user_id"]:
            continue
        if not (params["p_desde"] <= t["data_compra"] < params["p_ate"]):
            continue
        chave = (
            f"{t['data_compra'][:7]}-01",
            t.get("categoria_id"),
            t.get("subcategoria_id"),
            t.get("conta_id"),
            t.get("caixinha_id"),
            t.get("estrutura_custo"),
            t["tipo_movimento"],
        )
        grupos[chave] = grupos.get(chave, 0.0) + t["valor"]
    return [
        {
            "mes": mes,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id,
            "conta_id": conta_id,
            "caixinha_id": caixinha_id,
            "estrutura_custo": estrutura_custo,
            "tipo_movimento": tipo_movimento,
            "total": total,
        }
        for (mes, categoria_id, subcategoria_id, conta_id, caixinha_id, estrutura_custo, tipo_movimento), total in (
            grupos.items()
        )
    ]


# espelha as funções RPC de db/schema.sql (agregação no banco — ver
# comentário lá "AGREGAÇÕES EM RPC"). Cada fake opera sobre o mesmo
# `store["transacoes"]` que os testes já povoam via `.table(...)`/POST
# real, então nenhum teste precisa mudar como monta seus dados.
_FAKE_RPCS: dict[str, Callable[[list[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]]] = {
    "saldo_caixinhas": _fake_saldo_caixinhas,
    "resumo_agregado_transacoes": _fake_resumo_agregado_transacoes,
    "saldo_transacoes_agregado": _fake_saldo_transacoes_agregado,
}


class FakeRpc:
    def __init__(self, data: list[dict[str, Any]]):
        self._data = data

    def execute(self) -> FakeResult:
        return FakeResult(self._data)


class FakeSupabaseClient:
    """Substitui supabase.Client nos testes. `store` é compartilhado entre
    chamadas dentro de um mesmo teste para simular um banco persistente."""

    def __init__(self, store: dict[str, list[dict[str, Any]]]):
        self._store = store

    def table(self, name: str) -> FakeQuery:
        self._store.setdefault(name, [])
        return FakeQuery(self._store[name], table=name)

    def rpc(self, name: str, params: dict[str, Any]) -> FakeRpc:
        handler = _FAKE_RPCS.get(name)
        if handler is None:
            raise RuntimeError(f"RPC fake não implementada: {name!r}")
        return FakeRpc(handler(self._store.get("transacoes", []), params))
