"""Cálculo "ao vivo" de realizado e saldo_anterior de um item de orçamento
— usado tanto por routers/orcamentos.py (validação de teto, envelope de
cada item) quanto por routers/estrutura_custo.py (saldo acumulado por
bucket, teto do pool/piso).

saldo_anterior nunca é confiável direto da coluna gravada: ela só é
atualizada no momento em que "gerar próximo mês" roda, então editar ou
lançar algo no mês anterior DEPOIS de já ter gerado o mês seguinte deixa
esse valor congelado (era o bug reportado: item de agosto mudou, setembro
continuava com o saldo antigo até alguém clicar "gerar" de novo). Em vez
de gravar-e-confiar, cada leitura recalcula subindo a cadeia de meses
anteriores até achar o primeiro mês (sem orçamento anterior) ou um item
sem vínculo (categoria/subcategoria/conta — aí não tem como achar o
equivalente do mês anterior, mantém o valor gravado como estava)."""
from __future__ import annotations

from datetime import date

from supabase import Client

from .fatura import somar_meses

ITENS_TABLE = "orcamento_itens"

# mesmo sinal de orcamentos.py — despesa conta a favor do gasto,
# estorno/ressarcimento reduz (é dinheiro devolvido); aplicacao/retirada só
# entram para itens de investimento (via conta_vinculada_id)
_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def calcular_realizado_item(db: Client, user_id: str, item: dict, mes_inicio: date, mes_fim: date) -> float:
    """Soma as transações do período que contam para este item — por
    subcategoria/categoria para os buckets de custo, ou pela conta vinculada
    para itens de investimento. Sem nenhum dos três vínculos, não há como
    calcular realizado (o item é só uma linha de planejamento livre).

    Checa subcategoria antes de categoria: um item criado a partir da tela
    de Planejamento pode ter os dois campos preenchidos ao mesmo tempo
    (formulário sempre manda a categoria pai junto quando escolhe
    subcategoria), e filtrar por categoria primeiro puxaria transações de
    outras subcategorias da mesma categoria pai — mesma lógica de
    estrutura_custo._chave. A exclusão de subcategoria no caso "só
    categoria" é feita em Python (não com .is_() do postgrest) — mesmo
    filtro final, sem depender de mais um operador da query builder."""
    if item.get("subcategoria_id"):
        linhas = (
            db.table("transacoes")
            .select("valor,tipo_movimento")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("subcategoria_id", item["subcategoria_id"])
            .execute()
            .data
        )
    elif item.get("categoria_id"):
        candidatas = (
            db.table("transacoes")
            .select("valor,tipo_movimento,subcategoria_id")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("categoria_id", item["categoria_id"])
            .execute()
            .data
        )
        linhas = [t for t in candidatas if not t.get("subcategoria_id")]
    elif item.get("conta_vinculada_id"):
        linhas = (
            db.table("transacoes")
            .select("valor,tipo_movimento")
            .eq("user_id", user_id)
            .gte("data_compra", mes_inicio.isoformat())
            .lt("data_compra", mes_fim.isoformat())
            .eq("conta_id", item["conta_vinculada_id"])
            .execute()
            .data
        )
    else:
        return 0.0

    total = sum(_SINAL_REALIZADO.get(t["tipo_movimento"], 0) * t["valor"] for t in linhas)
    return round(total, 2)


def _item_equivalente_no_mes(db: Client, orcamento_id: str, item: dict) -> dict | None:
    """Acha, dentro de um orçamento de outro mês, o item do mesmo bucket
    com a mesma categoria/subcategoria/conta vinculada — o "mesmo envelope"
    em outro mês. Sem nenhum vínculo (item nome-livre) não há como achar,
    retorna None."""
    query = (
        db.table(ITENS_TABLE)
        .select("*")
        .eq("orcamento_id", orcamento_id)
        .eq("bucket", item["bucket"])
        .eq("ativo", True)
    )
    if item.get("subcategoria_id"):
        query = query.eq("subcategoria_id", item["subcategoria_id"])
    elif item.get("categoria_id"):
        query = query.eq("categoria_id", item["categoria_id"])
    elif item.get("conta_vinculada_id"):
        query = query.eq("conta_vinculada_id", item["conta_vinculada_id"])
    else:
        return None
    encontrados = query.execute().data
    return encontrados[0] if encontrados else None


def saldo_anterior_ao_vivo(
    db: Client,
    user_id: str,
    item: dict,
    vigencia_mes_item: date,
    cache: dict[tuple, float] | None = None,
) -> float:
    """saldo_anterior recalculado na hora, em vez de confiar na coluna
    gravada (congelada desde o último "gerar próximo mês"). Recursivo: sobe
    até achar o primeiro mês da cadeia (sem orçamento anterior) ou um item
    sem categoria/subcategoria/conta vinculada (nome livre — sem como achar
    o equivalente do mês anterior, mantém o valor gravado nesse caso)."""
    if cache is None:
        cache = {}

    sem_vinculo = not (item.get("subcategoria_id") or item.get("categoria_id") or item.get("conta_vinculada_id"))
    if sem_vinculo:
        return item.get("saldo_anterior", 0)

    chave_cache = (
        item.get("bucket"),
        item.get("categoria_id"),
        item.get("subcategoria_id"),
        item.get("conta_vinculada_id"),
        vigencia_mes_item.isoformat(),
    )
    if chave_cache in cache:
        return cache[chave_cache]

    mes_anterior = somar_meses(vigencia_mes_item, -1)
    orcamentos_anteriores = (
        db.table("orcamentos")
        .select("id")
        .eq("user_id", user_id)
        .eq("vigencia_mes", mes_anterior.isoformat())
        .execute()
        .data
    )
    if not orcamentos_anteriores:
        cache[chave_cache] = 0.0
        return 0.0

    item_anterior = _item_equivalente_no_mes(db, orcamentos_anteriores[0]["id"], item)
    if item_anterior is None:
        cache[chave_cache] = 0.0
        return 0.0

    saldo_do_anterior = saldo_anterior_ao_vivo(db, user_id, item_anterior, mes_anterior, cache)
    disponivel_anterior = round(item_anterior["orcamento_mensal"] + saldo_do_anterior, 2)
    mes_fim_anterior = somar_meses(mes_anterior, 1)
    realizado_anterior = calcular_realizado_item(db, user_id, item_anterior, mes_anterior, mes_fim_anterior)
    resultado = round(disponivel_anterior - realizado_anterior, 2)
    cache[chave_cache] = resultado
    return resultado
