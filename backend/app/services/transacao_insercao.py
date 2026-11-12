"""Inserção de uma linha em `transacoes` — compartilhado entre criação
manual (routers/transacoes.py) e a confirmação de um mês de lançamento
recorrente (routers/lancamentos_recorrentes.py): mesma tabela, mesma
regra de fatura de cartão e mesmo tratamento de duplicata."""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException
from supabase import Client

from .fatura import calcular_fatura_referencia

TABLE = "transacoes"


def fatura_referencia_para(db: Client, user_id: str, conta_id: str, data_compra: date) -> str | None:
    """Só se aplica a contas do tipo cartão de crédito com dia de
    fechamento configurado; para as demais, fica None (não se aplica)."""
    result = (
        db.table("contas")
        .select("tipo_conta,dia_fechamento")
        .eq("id", conta_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        return None
    conta = result.data[0]
    if conta["tipo_conta"] != "cartao_credito" or not conta["dia_fechamento"]:
        return None
    return calcular_fatura_referencia(data_compra, conta["dia_fechamento"]).isoformat()


def inserir_transacao(db: Client, row: dict[str, Any]) -> dict[str, Any]:
    try:
        result = db.table(TABLE).insert(row).execute()
    except Exception as exc:  # noqa: BLE001 — traduzimos a violação de unicidade conhecida; o resto vai pro log
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Já existe um lançamento idêntico (mesma data, valor, conta e descrição).",
            ) from exc
        print(f"[transacoes] falha ao inserir: {exc!r} — row={row}")
        raise HTTPException(status_code=500, detail="Falha ao salvar a transação") from exc
    return result.data[0]
