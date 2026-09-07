from datetime import date

from fastapi import APIRouter, Depends
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.estrutura_custo import EstruturaCustoMes
from ..services.fatura import somar_meses
from ..services.orcamento_teto import calcular_teto_bucket

router = APIRouter(prefix="/estrutura-custo", tags=["estrutura-custo"])

# os 3 buckets de gasto formam um teto agregado único (regra do pool):
# estourar um deles não compromete o mês se sobrar nos outros dois.
# investimentos fica de fora — não é teto, é piso (ver VereditoPiso).
_BUCKETS_POOL = ("custos_fixos", "custos_variaveis", "sazonalidades")

# mesmo vocabulário de bucket usado em orcamentos, +3 casos que só existem
# aqui: "investimentos" pega aplicacao/retirada vinculada a categoria de
# investimento, "reservas" pega aplicacao/retirada vinculada a caixinha
# (reserva não é investimento — sem teto/piso, só informativo) e
# "sem_estrutura" cobre despesas sem estrutura_custo preenchida — visível
# de propósito, em vez de sumir da soma (diagnóstico de qualidade de dados)
_BUCKET_POR_ESTRUTURA = {
    "fixo": "custos_fixos",
    "variavel": "custos_variaveis",
    "sazonal": "sazonalidades",
}
_BUCKETS = ("custos_fixos", "custos_variaveis", "sazonalidades", "investimentos", "reservas", "sem_estrutura")

_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def _bucket_da_transacao(t: dict) -> str:
    if t["tipo_movimento"] in ("aplicacao", "retirada"):
        return "reservas" if t.get("caixinha_id") else "investimentos"
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
    saldo_anterior_por_bucket: dict[str, float] = {}
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
            saldo_anterior_por_bucket[item["bucket"]] = (
                saldo_anterior_por_bucket.get(item["bucket"], 0) + item.get("saldo_anterior", 0)
            )

    transacoes = (
        db.table("transacoes")
        .select("valor,tipo_movimento,estrutura_custo,categoria_id,subcategoria_id,conta_id,caixinha_id")
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

    buckets = {
        b: {
            "bucket": b,
            "orcado": 0.0,
            "realizado": 0.0,
            "itens": [],
            "saldo_anterior_acumulado": round(saldo_anterior_por_bucket.get(b, 0), 2),
        }
        for b in _BUCKETS
    }
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

    pool_despesas = None
    piso_investimentos = None
    if orcamento:
        teto_pool = sum(calcular_teto_bucket(orcamento, b) for b in _BUCKETS_POOL) + sum(
            saldo_anterior_por_bucket.get(b, 0) for b in _BUCKETS_POOL
        )
        realizado_pool = round(sum(buckets[b]["realizado"] for b in _BUCKETS_POOL), 2)
        pool_despesas = {
            "teto": round(teto_pool, 2),
            "realizado": realizado_pool,
            "dentro_do_teto": realizado_pool <= teto_pool + 0.005,
        }

        teto_investimentos = calcular_teto_bucket(orcamento, "investimentos") + saldo_anterior_por_bucket.get(
            "investimentos", 0
        )
        realizado_investimentos = buckets["investimentos"]["realizado"]
        piso_investimentos = {
            "teto": round(teto_investimentos, 2),
            "realizado": realizado_investimentos,
            "meta_batida": realizado_investimentos >= teto_investimentos - 0.005,
        }

    return {
        "vigencia_mes": mes_inicio.isoformat(),
        "orcamento_id": orcamento["id"] if orcamento else None,
        "buckets": [buckets[b] for b in _BUCKETS],
        "pool_despesas": pool_despesas,
        "piso_investimentos": piso_investimentos,
    }
