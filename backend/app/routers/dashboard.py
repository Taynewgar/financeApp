from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.dashboard import (
    CompromissoFuturo,
    DespesaPorCategoria,
    DespesaPorSubcategoria,
    EvolucaoMensal,
    PrimeiroMes,
    ResumoMensal,
    ResumoPeriodo,
    SaldoCaixinha,
)
from ..services.crud import buscar_todas_paginado
from ..services.fatura import somar_meses
from ..services.recorrentes import data_ocorrencia, proxima_ocorrencia_pendente
from ..services.resumo_financeiro import calcular_resumo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_MESES_MAXIMO_NA_EVOLUCAO = 60  # 5 anos — limite defensivo contra range gigante por engano


def _resumo_entre(db: Client, user_id: str, data_inicio: date, data_fim_exclusiva: date) -> dict:
    # paginado: usado tanto por /mensal (1 mês, sempre pequeno) quanto por
    # /resumo-periodo no modo "Todos os meses" (histórico inteiro — já
    # passou de 1000 transações numa conta real, ver buscar_todas_paginado)
    transacoes = buscar_todas_paginado(
        lambda: db.table("transacoes")
        .select("valor,tipo_movimento,ajuste_de_transacao_id,caixinha_id")
        .eq("user_id", user_id)
        .gte("data_compra", data_inicio.isoformat())
        .lt("data_compra", data_fim_exclusiva.isoformat())
    )
    return calcular_resumo(transacoes)


def _resumo_do_mes(db: Client, user_id: str, mes_inicio: date) -> dict:
    resumo = _resumo_entre(db, user_id, mes_inicio, somar_meses(mes_inicio, 1))
    resumo["vigencia_mes"] = mes_inicio.isoformat()
    return resumo


@router.get("/mensal/{vigencia_mes}", response_model=ResumoMensal)
def resumo_mensal(vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    resumo = _resumo_do_mes(db, user_id, mes_inicio)
    resumo.pop("_receita_ajustada")
    return resumo


@router.get("/evolucao", response_model=EvolucaoMensal)
def evolucao_mensal(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fim = date(fim.year, fim.month, 1)
    if mes_fim < mes_inicio:
        raise HTTPException(status_code=422, detail="'fim' não pode ser anterior a 'inicio'")

    total_meses = (mes_fim.year - mes_inicio.year) * 12 + (mes_fim.month - mes_inicio.month) + 1
    if total_meses > _MESES_MAXIMO_NA_EVOLUCAO:
        raise HTTPException(status_code=422, detail=f"Intervalo maior que {_MESES_MAXIMO_NA_EVOLUCAO} meses")

    # busca o período INTEIRO numa query só (perf — antes era 1 SELECT em
    # transacoes POR MÊS do loop, ~O(meses) idas e voltas sequenciais ao
    # Supabase; ver Rodada 2026-09-22, mesmo motivo do fix em
    # estrutura_custo.evolucao_orcamento) e agrupa por mês em Python antes
    # de agregar cada um com calcular_resumo (já é uma função pura, não
    # depende do banco).
    mes_fim_exclusivo = somar_meses(mes_fim, 1)
    todas_transacoes = buscar_todas_paginado(
        lambda: db.table("transacoes")
        .select("valor,tipo_movimento,ajuste_de_transacao_id,caixinha_id,data_compra")
        .eq("user_id", user_id)
        .gte("data_compra", mes_inicio.isoformat())
        .lt("data_compra", mes_fim_exclusivo.isoformat())
    )
    transacoes_por_mes: dict[str, list[dict]] = {}
    for t in todas_transacoes:
        chave_mes = f"{t['data_compra'][:7]}-01"
        transacoes_por_mes.setdefault(chave_mes, []).append(t)

    resultado_acumulado = 0.0
    receita_ajustada_acumulada = 0.0
    meses = []
    mes_atual = mes_inicio
    while mes_atual <= mes_fim:
        resumo = calcular_resumo(transacoes_por_mes.get(mes_atual.isoformat(), []))
        resumo["vigencia_mes"] = mes_atual.isoformat()
        receita_ajustada = resumo.pop("_receita_ajustada")
        resultado_acumulado = round(resultado_acumulado + resumo["resultado_saude"], 2)
        receita_ajustada_acumulada = round(receita_ajustada_acumulada + receita_ajustada, 2)
        resumo["resultado_saude_acumulado"] = resultado_acumulado
        resumo["taxa_poupanca_acumulada"] = (
            round(resultado_acumulado / receita_ajustada_acumulada * 100, 2)
            if receita_ajustada_acumulada
            else None
        )
        meses.append(resumo)
        mes_atual = somar_meses(mes_atual, 1)

    return {"inicio": mes_inicio.isoformat(), "fim": mes_fim.isoformat(), "meses": meses}


@router.get("/resumo-periodo", response_model=ResumoPeriodo)
def resumo_periodo(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mesmo resumo de /mensal, mas somado sobre um período livre — usado
    pelo seletor do Dashboard nos modos Intervalo/Todos os meses. Soma as
    transações do período inteiro de uma vez (não é a soma dos resumos
    mensais): taxa_poupanca precisa ser recalculada sobre o total do
    período, senão vira uma média de taxas que não bate com o total real."""
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fim_exclusiva = somar_meses(date(fim.year, fim.month, 1), 1)
    if mes_fim_exclusiva <= mes_inicio:
        raise HTTPException(status_code=422, detail="'fim' não pode ser anterior a 'inicio'")

    resumo = _resumo_entre(db, user_id, mes_inicio, mes_fim_exclusiva)
    resumo.pop("_receita_ajustada")
    resumo["inicio"] = mes_inicio.isoformat()
    resumo["fim"] = date(fim.year, fim.month, 1).isoformat()
    return resumo


@router.get("/primeiro-mes", response_model=PrimeiroMes)
def primeiro_mes(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Mês do lançamento mais antigo do usuário — base do modo "Todos os
    meses" do seletor do Dashboard (sem isso não tem como saber onde o
    intervalo "todos" deveria começar)."""
    transacoes = (
        db.table("transacoes")
        .select("data_compra")
        .eq("user_id", user_id)
        .order("data_compra")
        .execute()
        .data
    )
    if not transacoes:
        return {"vigencia_mes": None}
    primeira_data = transacoes[0]["data_compra"]
    return {"vigencia_mes": f"{primeira_data[:7]}-01"}


def _despesas_por_categoria_entre(
    db: Client, user_id: str, data_inicio: date, data_fim_exclusiva: date
) -> list[dict]:
    despesas = buscar_todas_paginado(
        lambda: db.table("transacoes")
        .select("categoria_id,valor")
        .eq("user_id", user_id)
        .eq("tipo_movimento", "despesa")
        .gte("data_compra", data_inicio.isoformat())
        .lt("data_compra", data_fim_exclusiva.isoformat())
    )
    if not despesas:
        return []

    totais: dict[str, float] = {}
    for d in despesas:
        categoria_id = d["categoria_id"]
        totais[categoria_id] = totais.get(categoria_id, 0.0) + d["valor"]
    total_geral = sum(totais.values())

    categorias = db.table("categorias").select("id,nome").eq("user_id", user_id).execute().data
    nomes = {c["id"]: c["nome"] for c in categorias}

    resultado = [
        {
            "categoria_id": categoria_id,
            "categoria_nome": nomes.get(categoria_id, "Sem categoria"),
            "valor": round(valor, 2),
            "percentual": round(valor / total_geral * 100, 2) if total_geral else 0.0,
        }
        for categoria_id, valor in totais.items()
    ]
    resultado.sort(key=lambda r: r["valor"], reverse=True)
    return resultado


@router.get("/despesas-por-categoria/{vigencia_mes}", response_model=list[DespesaPorCategoria])
def despesas_por_categoria(
    vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    """Despesas do mês agrupadas por categoria PAI (não subcategoria — essa
    quebra mais fina fica pra Estrutura de Custo). Usa despesa bruta (sem
    descontar estorno/ressarcimento vinculado), igual `despesas_brutas` do
    resumo — mostra onde o dinheiro foi gasto, não o líquido."""
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    mes_fim = somar_meses(mes_inicio, 1)
    return _despesas_por_categoria_entre(db, user_id, mes_inicio, mes_fim)


@router.get("/despesas-por-categoria-periodo", response_model=list[DespesaPorCategoria])
def despesas_por_categoria_periodo(
    inicio: date = Query(...),
    fim: date = Query(...),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mesma agregação de /despesas-por-categoria/{vigencia_mes}, mas somada
    sobre um período livre — usado pelos modos Intervalo/Todos os meses do
    seletor (mesmo padrão de /resumo-periodo vs /mensal)."""
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fim_exclusiva = somar_meses(date(fim.year, fim.month, 1), 1)
    if mes_fim_exclusiva <= mes_inicio:
        raise HTTPException(status_code=422, detail="'fim' não pode ser anterior a 'inicio'")
    return _despesas_por_categoria_entre(db, user_id, mes_inicio, mes_fim_exclusiva)


def _despesas_por_subcategoria_entre(
    db: Client, user_id: str, data_inicio: date, data_fim_exclusiva: date, categoria_id: str | None
) -> list[dict]:
    def construir_query():
        query = (
            db.table("transacoes")
            .select("subcategoria_id,categoria_id,valor")
            .eq("user_id", user_id)
            .eq("tipo_movimento", "despesa")
            .gte("data_compra", data_inicio.isoformat())
            .lt("data_compra", data_fim_exclusiva.isoformat())
        )
        if categoria_id:
            query = query.eq("categoria_id", categoria_id)
        return query

    despesas = buscar_todas_paginado(construir_query)
    if not despesas:
        return []

    totais: dict[str, float] = {}
    for d in despesas:
        chave = d["subcategoria_id"] or "sem-subcategoria"
        totais[chave] = totais.get(chave, 0.0) + d["valor"]
    total_geral = sum(totais.values())

    subcategorias = db.table("subcategorias").select("id,nome").eq("user_id", user_id).execute().data
    nomes = {s["id"]: s["nome"] for s in subcategorias}

    resultado = [
        {
            "subcategoria_id": None if chave == "sem-subcategoria" else chave,
            "subcategoria_nome": "Sem subcategoria" if chave == "sem-subcategoria" else nomes.get(chave, "Sem subcategoria"),
            "valor": round(valor, 2),
            "percentual": round(valor / total_geral * 100, 2) if total_geral else 0.0,
        }
        for chave, valor in totais.items()
    ]
    resultado.sort(key=lambda r: r["valor"], reverse=True)
    return resultado


@router.get("/despesas-por-subcategoria/{vigencia_mes}", response_model=list[DespesaPorSubcategoria])
def despesas_por_subcategoria(
    vigencia_mes: date,
    categoria_id: str | None = None,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mesma ideia de /despesas-por-categoria, mas por subcategoria — usado
    pelo Pareto na quebra mais fina. `categoria_id` filtra pra só as
    subcategorias daquela categoria pai (Pareto de subcategoria, igual ao
    seletor de categoria pai do app original); sem filtro, mistura
    subcategorias de todas as categorias."""
    mes_inicio = date(vigencia_mes.year, vigencia_mes.month, 1)
    mes_fim = somar_meses(mes_inicio, 1)
    return _despesas_por_subcategoria_entre(db, user_id, mes_inicio, mes_fim, categoria_id)


@router.get("/despesas-por-subcategoria-periodo", response_model=list[DespesaPorSubcategoria])
def despesas_por_subcategoria_periodo(
    inicio: date = Query(...),
    fim: date = Query(...),
    categoria_id: str | None = None,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mesma agregação de /despesas-por-subcategoria/{vigencia_mes}, mas
    somada sobre um período livre — mesmo padrão de /despesas-por-categoria-
    periodo."""
    mes_inicio = date(inicio.year, inicio.month, 1)
    mes_fim_exclusiva = somar_meses(date(fim.year, fim.month, 1), 1)
    if mes_fim_exclusiva <= mes_inicio:
        raise HTTPException(status_code=422, detail="'fim' não pode ser anterior a 'inicio'")
    return _despesas_por_subcategoria_entre(db, user_id, mes_inicio, mes_fim_exclusiva, categoria_id)


@router.get("/patrimonio/{vigencia_mes}", response_model=list[SaldoCaixinha])
def patrimonio_caixinhas(
    vigencia_mes: date, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    """Saldo de cada caixinha ativa, acumulado (aplicações menos retiradas
    desde sempre) até o fim do mês selecionado — permite ver o patrimônio
    histórico ao navegar por meses passados, não só o saldo atual. Contas
    ainda não têm saldo próprio (só `saldo_inicial` estático), então esse
    "patrimônio" cobre só caixinhas por enquanto."""
    mes_fim = somar_meses(date(vigencia_mes.year, vigencia_mes.month, 1), 1)
    caixinhas = (
        db.table("caixinhas")
        .select("id,nome")
        .eq("user_id", user_id)
        .eq("ativo", True)
        .order("nome")
        .execute()
        .data
    )
    if not caixinhas:
        return []

    # sem filtro de data de início ("desde sempre") nem .order() — o pior
    # caso pro limite de 1000 linhas do Supabase: sem paginação, perde
    # linhas de forma imprevisível (achado 2026-09-25, ver
    # buscar_todas_paginado)
    movimentos = buscar_todas_paginado(
        lambda: db.table("transacoes")
        .select("caixinha_id,valor,tipo_movimento")
        .eq("user_id", user_id)
        .lt("data_compra", mes_fim.isoformat())
    )
    saldos = {c["id"]: 0.0 for c in caixinhas}
    for m in movimentos:
        caixinha_id = m.get("caixinha_id")
        if caixinha_id not in saldos:
            continue
        saldos[caixinha_id] += m["valor"] if m["tipo_movimento"] == "aplicacao" else -m["valor"]

    return [{"id": c["id"], "nome": c["nome"], "saldo": round(saldos[c["id"]], 2)} for c in caixinhas]


@router.get("/compromissos-futuros", response_model=list[CompromissoFuturo])
def compromissos_futuros(
    limite: int = Query(5, ge=1, le=100),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mistura 2 fontes de compromisso em aberto:

    1. Próxima parcela em aberto de cada compra parcelada ativa — as
       parcelas futuras já estão materializadas na tabela (ver
       POST /transacoes/parceladas), só filtra o que ainda não venceu.
    2. Próxima ocorrência PENDENTE de cada lançamento recorrente ativo —
       despesa fixa recorrente (aluguel, assinatura), projeção virtual:
       nada é gravado em transacoes até confirmar (ver
       services/recorrentes.py e POST
       /lancamentos-recorrentes/{id}/confirmar). Pode ser um mês já
       vencido, se ficou sem confirmar — fica aparecendo até o usuário
       confirmar, marcar como pulado (POST .../pular — ex: viajou, não
       teve a despesa naquele mês) ou desativar o recorrente, é assim que
       o "compromisso em aberto" some da lista."""
    hoje = date.today()
    parcelas = (
        db.table("transacoes")
        .select("descricao,valor,data_compra,parcela_atual,parcela_total,compra_parcelada_id")
        .eq("user_id", user_id)
        .eq("pagamento", "parcelado")
        .gt("data_compra", hoje.isoformat())
        .order("data_compra")
        .execute()
        .data
    )
    vistos: set[str] = set()
    itens: list[dict] = []
    for parcela in parcelas:
        grupo = parcela["compra_parcelada_id"]
        if grupo in vistos:
            continue
        vistos.add(grupo)
        itens.append(
            {
                "tipo": "parcela",
                "descricao": parcela["descricao"],
                "valor": parcela["valor"],
                "data_compra": parcela["data_compra"],
                "tipo_movimento": "despesa",
                "parcela_atual": parcela["parcela_atual"],
                "parcela_total": parcela["parcela_total"],
                "lancamento_recorrente_id": None,
            }
        )

    recorrentes = (
        db.table("lancamentos_recorrentes").select("*").eq("user_id", user_id).eq("ativo", True).execute().data
    )
    recorrente_ids = [r["id"] for r in recorrentes]
    confirmados_por_recorrente: dict[str, set[str]] = {rid: set() for rid in recorrente_ids}
    if recorrente_ids:
        confirmados = (
            db.table("transacoes")
            .select("lancamento_recorrente_id,data_compra")
            .eq("user_id", user_id)
            .in_("lancamento_recorrente_id", recorrente_ids)
            .execute()
            .data
        )
        for c in confirmados:
            confirmados_por_recorrente[c["lancamento_recorrente_id"]].add(f"{c['data_compra'][:7]}-01")

    pulados_por_recorrente: dict[str, set[str]] = {rid: set() for rid in recorrente_ids}
    if recorrente_ids:
        pulados = (
            db.table("lancamentos_recorrentes_pulados")
            .select("lancamento_recorrente_id,vigencia_mes")
            .in_("lancamento_recorrente_id", recorrente_ids)
            .execute()
            .data
        )
        for p in pulados:
            pulados_por_recorrente[p["lancamento_recorrente_id"]].add(p["vigencia_mes"])

    for recorrente in recorrentes:
        vigencia_pendente = proxima_ocorrencia_pendente(
            recorrente, confirmados_por_recorrente[recorrente["id"]], pulados_por_recorrente[recorrente["id"]]
        )
        if vigencia_pendente is None:
            continue
        itens.append(
            {
                "tipo": "recorrente",
                "descricao": recorrente["descricao"],
                "valor": recorrente["valor"],
                "data_compra": data_ocorrencia(vigencia_pendente, recorrente["dia_mes"]).isoformat(),
                "tipo_movimento": recorrente["tipo_movimento"],
                "parcela_atual": None,
                "parcela_total": None,
                "lancamento_recorrente_id": recorrente["id"],
            }
        )

    itens.sort(key=lambda i: i["data_compra"])
    return itens[:limite]
