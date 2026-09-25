from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.estrutura_custo import EstruturaCustoMes, TendenciaOrcamento
from ..services.fatura import somar_meses
from ..services.orcamento_saldo import carregar_dados_periodo, saldo_anterior_em_lote
from ..services.orcamento_teto import calcular_teto_bucket

router = APIRouter(prefix="/estrutura-custo", tags=["estrutura-custo"])

_MESES_MAXIMO_NA_EVOLUCAO = 60  # 5 anos — mesmo limite defensivo de /dashboard/evolucao

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
    na ordem subcategoria > categoria > conta vinculada. Subcategoria vem
    primeiro porque, num lançamento, categoria_id e subcategoria_id não são
    mutuamente exclusivos — escolher uma subcategoria sempre grava a
    categoria pai junto (NovoLancamento.tsx), então checar categoria
    primeiro faria todo lançamento com subcategoria cair na categoria pai e
    a subcategoria nunca aparecer como item próprio."""
    if registro.get("subcategoria_id"):
        return ("subcategoria", registro["subcategoria_id"])
    if registro.get("categoria_id"):
        return ("categoria", registro["categoria_id"])
    if registro.get(campo_conta):
        return ("conta", registro[campo_conta])
    return ("sem_vinculo", None)


def _agregar_estrutura_custo(
    mes_inicio: date,
    orcamento: dict | None,
    itens_orcamento: list[dict],
    transacoes: list[dict],
    saldo_anterior_de: Callable[[dict], float],
) -> dict:
    """Monta o resultado de 1 mês (buckets, pool_despesas,
    piso_investimentos) a partir de dados JÁ CARREGADOS — sem nenhuma
    consulta ao banco aqui dentro. `saldo_anterior_de(item)` é injetado
    pelo chamador — hoje sempre `saldo_anterior_em_lote` (100% em memória
    sobre dado pré-carregado por `carregar_dados_periodo`), usada tanto
    por `obter()` (1 mês) quanto por `evolucao_orcamento()` (vários) —
    ver Rodada 2026-09-22 (perf de /graficos) e Rodada 27 (mesmo fix
    estendido a `obter()`, que até então recalculava a cadeia de
    saldo_anterior item a item direto no banco)."""
    orcado_por_chave: dict[tuple, float] = {}
    orcamento_mensal_por_chave: dict[tuple, float] = {}
    saldo_anterior_por_chave: dict[tuple, float] = {}
    saldo_anterior_por_bucket: dict[str, float] = {}
    for item in itens_orcamento:
        # saldo_anterior recalculado ao vivo, não a coluna gravada — mesmo
        # motivo de orcamentos._enriquecer_item: fica congelado desde o
        # último "gerar próximo mês", editar/lançar algo no mês anterior
        # depois disso não devia exigir gerar de novo.
        saldo_anterior_item = saldo_anterior_de(item)
        chave_completa = (item["bucket"], _chave(item, "conta_vinculada_id"))
        disponivel = round(item["orcamento_mensal"] + saldo_anterior_item, 2)
        orcado_por_chave[chave_completa] = orcado_por_chave.get(chave_completa, 0) + disponivel
        orcamento_mensal_por_chave[chave_completa] = (
            orcamento_mensal_por_chave.get(chave_completa, 0) + item["orcamento_mensal"]
        )
        saldo_anterior_por_chave[chave_completa] = (
            saldo_anterior_por_chave.get(chave_completa, 0) + saldo_anterior_item
        )
        saldo_anterior_por_bucket[item["bucket"]] = (
            saldo_anterior_por_bucket.get(item["bucket"], 0) + saldo_anterior_item
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
                "orcamento_mensal": round(orcamento_mensal_por_chave.get(chave_completa, 0), 2),
                "saldo_anterior": round(saldo_anterior_por_chave.get(chave_completa, 0), 2),
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


def _estrutura_custo_do_mes_em_lote(
    mes_inicio: date,
    orcamento_por_mes: dict[str, dict],
    itens_por_orcamento_id: dict[str, list[dict]],
    transacoes_por_mes: dict[str, list[dict]],
    cache_saldo: dict,
) -> dict:
    """Monta 1 mês a partir de dados JÁ CARREGADOS em lote por
    `carregar_dados_periodo` (services/orcamento_saldo.py — usada por
    `obter()`, 1 mês, e `evolucao_orcamento()`, vários) — sem nenhuma
    consulta ao banco aqui dentro."""
    orcamento = orcamento_por_mes.get(mes_inicio.isoformat())
    itens_orcamento = itens_por_orcamento_id.get(orcamento["id"], []) if orcamento else []
    transacoes = transacoes_por_mes.get(mes_inicio.isoformat(), [])

    def saldo_anterior_de(item: dict) -> float:
        return saldo_anterior_em_lote(
            item, mes_inicio, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo
        )

    return _agregar_estrutura_custo(mes_inicio, orcamento, itens_orcamento, transacoes, saldo_anterior_de)


@router.get("/{vigencia_mes}", response_model=EstruturaCustoMes)
def obter(vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes = carregar_dados_periodo(
        db, user_id, mes_inicio, mes_inicio
    )
    return _estrutura_custo_do_mes_em_lote(
        mes_inicio, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo={}
    )


@router.get("/evolucao/tendencia", response_model=TendenciaOrcamento)
def evolucao_orcamento(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Orçado x realizado em vários meses — complementa a leitura de 1 mês
    só que /estrutura-custo/{mes} já dá. Escopo igual ao KPI "Orçado no mês"
    da tela (só o pool de despesas: custos_fixos + custos_variaveis +
    sazonalidades — investimentos é piso, não teto, ver rodada 2026-09-15).
    Rota de 2 segmentos (/evolucao/tendencia) de propósito — um só
    segmento colidiria com /{vigencia_mes}, que tenta interpretar
    qualquer path de 1 nível como data."""
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fim = date(fim.year, fim.month, 1)
    if mes_fim < mes_inicio:
        raise HTTPException(status_code=422, detail="'fim' não pode ser anterior a 'inicio'")

    total_meses = (mes_fim.year - mes_inicio.year) * 12 + (mes_fim.month - mes_inicio.month) + 1
    if total_meses > _MESES_MAXIMO_NA_EVOLUCAO:
        raise HTTPException(status_code=422, detail=f"Intervalo maior que {_MESES_MAXIMO_NA_EVOLUCAO} meses")

    # busca o período INTEIRO de uma vez (perf — antes era 1 SELECT em cada
    # uma das 3 tabelas POR MÊS do loop, ~O(meses) idas e voltas sequenciais
    # ao Supabase; ver Rodada 2026-09-22) — mesmo helper que `obter()` usa
    # pra 1 mês só (Rodada 27).
    orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes = carregar_dados_periodo(
        db, user_id, mes_inicio, mes_fim
    )

    meses = []
    mes_atual = mes_inicio
    # cache compartilhado entre TODOS os meses do período — sem isso, cada
    # mês recalcula a cadeia de saldo_anterior inteira do zero (perf: ver
    # docstring de saldo_anterior_em_lote)
    cache_saldo: dict = {}
    while mes_atual <= mes_fim:
        estrutura = _estrutura_custo_do_mes_em_lote(
            mes_atual, orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, cache_saldo
        )
        buckets_por_nome = {b["bucket"]: b for b in estrutura["buckets"]}
        orcado = round(sum(buckets_por_nome[b]["orcado"] for b in _BUCKETS_POOL), 2)
        realizado = round(sum(buckets_por_nome[b]["realizado"] for b in _BUCKETS_POOL), 2)
        meses.append(
            {
                "vigencia_mes": mes_atual.isoformat(),
                "orcado": orcado,
                "realizado": realizado,
                "percentual_executado": round(realizado / orcado * 100, 2) if orcado else None,
            }
        )
        mes_atual = somar_meses(mes_atual, 1)

    return {"inicio": mes_inicio.isoformat(), "fim": mes_fim.isoformat(), "meses": meses}
