from datetime import date

from fastapi import APIRouter, Depends
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.estrutura_custo import EstruturaCustoMes
from ..services.fatura import somar_meses

router = APIRouter(prefix="/estrutura-custo", tags=["estrutura-custo"])

# mesmo vocabulário de bucket usado em orcamentos, +2 casos que só existem
# aqui: "investimentos" pega aplicacao/retirada (sem estrutura_custo própria)
# e "sem_estrutura" cobre despesas sem estrutura_custo preenchida — visível
# de propósito, em vez de sumir da soma (diagnóstico de qualidade de dados)
_BUCKET_POR_ESTRUTURA = {
    "fixo": "custos_fixos",
    "variavel": "custos_variaveis",
    "sazonal": "sazonalidades",
}
_BUCKETS = ("custos_fixos", "custos_variaveis", "sazonalidades", "investimentos", "sem_estrutura")

_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def _bucket_da_transacao(t: dict) -> str:
    if t["tipo_movimento"] in ("aplicacao", "retirada"):
        return "investimentos"
    if t.get("estrutura_custo"):
        return _BUCKET_POR_ESTRUTURA[t["estrutura_custo"]]
    return "sem_estrutura"


def _chave(registro: dict, campo_conta: str) -> tuple[str, str | None]:
    """Identifica a que item um lançamento ou item de orçamento pertence,
    na ordem categoria > subcategoria > conta vinculada (mesma prioridade
    usada em orcamentos._calcular_realizado)."""
    if registro.get("categoria_id"):
        return ("categoria", registro["categoria_id"])
    if registro.get("subcategoria_id"):
        return ("subcategoria", registro["subcategoria_id"])
    if registro.get(campo_conta):
        return ("conta", registro[campo_conta])
    return ("sem_vinculo", None)


@router.get("/{vigencia_mes}", response_model=EstruturaCustoMes)
def obter(vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Compara orçado x realizado do mês, agrupado pelos mesmos buckets do
    orçamento. Funciona mesmo sem orçamento configurado para o mês (orcado
    fica 0) — a leitura de realizado não depende de planejamento prévio."""
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    mes_fim = somar_meses(mes_inicio, 1)

    orcamento_result = (
        db.table("orcamentos")
        .select("*")
        .eq("user_id", user_id)
        .eq("vigencia_mes", mes_inicio.isoformat())
        .execute()
    )
    orcamento = orcamento_result.data[0] if orcamento_result.data else None

    orcado_por_chave: dict[tuple, float] = {}
    if orcamento:
        itens_orcamento = (
            db.table("orcamento_itens")
            .select("*")
            .eq("orcamento_id", orcamento["id"])
            .eq("ativo", True)
            .execute()
            .data
        )
        for item in itens_orcamento:
            chave_completa = (item["bucket"], _chave(item, "conta_vinculada_id"))
            disponivel = round(item["orcamento_mensal"] + item.get("saldo_anterior", 0), 2)
            orcado_por_chave[chave_completa] = orcado_por_chave.get(chave_completa, 0) + disponivel

    transacoes = (
        db.table("transacoes")
        .select("valor,tipo_movimento,estrutura_custo,categoria_id,subcategoria_id,conta_id")
        .eq("user_id", user_id)
        .gte("data_compra", mes_inicio.isoformat())
        .lt("data_compra", mes_fim.isoformat())
        .execute()
        .data
    )

    realizado_por_chave: dict[tuple, float] = {}
    for t in transacoes:
        if t["tipo_movimento"] == "receita":
            continue
        chave_completa = (_bucket_da_transacao(t), _chave(t, "conta_id"))
        sinal = _SINAL_REALIZADO.get(t["tipo_movimento"], 0)
        realizado_por_chave[chave_completa] = realizado_por_chave.get(chave_completa, 0) + sinal * t["valor"]

    buckets = {b: {"bucket": b, "orcado": 0.0, "realizado": 0.0, "itens": []} for b in _BUCKETS}
    for chave_completa in set(orcado_por_chave) | set(realizado_por_chave):
        bucket, (tipo_chave, valor_chave) = chave_completa
        orcado = round(orcado_por_chave.get(chave_completa, 0), 2)
        realizado = round(realizado_por_chave.get(chave_completa, 0), 2)

        buckets[bucket]["itens"].append(
            {
                "categoria_id": valor_chave if tipo_chave == "categoria" else None,
                "subcategoria_id": valor_chave if tipo_chave == "subcategoria" else None,
                "conta_id": valor_chave if tipo_chave == "conta" else None,
                "orcado": orcado,
                "realizado": realizado,
            }
        )
        buckets[bucket]["orcado"] = round(buckets[bucket]["orcado"] + orcado, 2)
        buckets[bucket]["realizado"] = round(buckets[bucket]["realizado"] + realizado, 2)

    return {
        "vigencia_mes": mes_inicio.isoformat(),
        "orcamento_id": orcamento["id"] if orcamento else None,
        "buckets": [buckets[b] for b in _BUCKETS],
    }
