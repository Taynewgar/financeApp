from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.dashboard import (
    CompromissoFuturo,
    DespesaPorCategoria,
    EvolucaoMensal,
    PrimeiroMes,
    ResumoMensal,
    ResumoPeriodo,
    SaldoCaixinha,
)
from ..services.fatura import somar_meses
from ..services.resumo_financeiro import calcular_resumo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_MESES_MAXIMO_NA_EVOLUCAO = 60  # 5 anos — limite defensivo contra range gigante por engano


def _resumo_entre(db: Client, user_id: str, data_inicio: date, data_fim_exclusiva: date) -> dict:
    transacoes = (
        db.table("transacoes")
        .select("valor,tipo_movimento,ajuste_de_transacao_id,caixinha_id")
        .eq("user_id", user_id)
        .gte("data_compra", data_inicio.isoformat())
        .lt("data_compra", data_fim_exclusiva.isoformat())
        .execute()
        .data
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

    resultado_acumulado = 0.0
    receita_ajustada_acumulada = 0.0
    meses = []
    mes_atual = mes_inicio
    while mes_atual <= mes_fim:
        resumo = _resumo_do_mes(db, user_id, mes_atual)
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
    despesas = (
        db.table("transacoes")
        .select("categoria_id,valor")
        .eq("user_id", user_id)
        .eq("tipo_movimento", "despesa")
        .gte("data_compra", data_inicio.isoformat())
        .lt("data_compra", data_fim_exclusiva.isoformat())
        .execute()
        .data
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

    movimentos = (
        db.table("transacoes")
        .select("caixinha_id,valor,tipo_movimento")
        .eq("user_id", user_id)
        .lt("data_compra", mes_fim.isoformat())
        .execute()
        .data
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
    limite: int = Query(5, ge=1, le=20),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Próxima parcela em aberto de cada compra parcelada ativa — as
    parcelas futuras já estão materializadas na tabela (ver
    POST /transacoes/parceladas), então isso é só filtrar o que ainda não
    venceu e pegar a mais próxima de cada grupo. Não inclui despesas fixas
    recorrentes (aluguel, assinaturas): esse conceito não existe no app —
    não há cadastro de "lançamento recorrente" separado de uma transação já
    lançada, só compra parcelada tem data futura conhecida de antemão."""
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
    resultado = []
    for parcela in parcelas:
        grupo = parcela["compra_parcelada_id"]
        if grupo in vistos:
            continue
        vistos.add(grupo)
        resultado.append(parcela)
        if len(resultado) >= limite:
            break
    return resultado
