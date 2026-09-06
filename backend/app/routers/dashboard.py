from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.dashboard import EvolucaoMensal, ResumoMensal
from ..services.fatura import somar_meses
from ..services.resumo_financeiro import calcular_resumo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_MESES_MAXIMO_NA_EVOLUCAO = 60  # 5 anos — limite defensivo contra range gigante por engano


def _resumo_do_mes(db: Client, user_id: str, mes_inicio: date) -> dict:
    mes_fim = somar_meses(mes_inicio, 1)
    transacoes = (
        db.table("transacoes")
        .select("valor,tipo_movimento,ajuste_de_transacao_id")
        .eq("user_id", user_id)
        .gte("data_compra", mes_inicio.isoformat())
        .lt("data_compra", mes_fim.isoformat())
        .execute()
        .data
    )
    resumo = calcular_resumo(transacoes)
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
