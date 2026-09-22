from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.lancamentos_recorrentes import (
    LancamentoRecorrente,
    LancamentoRecorrenteCreate,
    LancamentoRecorrenteUpdate,
    MesPulado,
    VigenciaMesPayload,
)
from ..schemas.transacoes import Transacao
from ..services import crud
from ..services.dedup import compute_hash
from ..services.fatura import somar_meses
from ..services.orcamento_sync import sincronizar_item_orcamento
from ..services.recorrentes import data_ocorrencia
from ..services.transacao_insercao import fatura_referencia_para, inserir_transacao

router = APIRouter(prefix="/lancamentos-recorrentes", tags=["lancamentos-recorrentes"])
TABLE = "lancamentos_recorrentes"


def _check_refs(db: Client, user_id: str, conta_id: str, categoria_id: str, subcategoria_id: str | None) -> None:
    if not crud.get_owned(db, "contas", user_id, conta_id):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    if not crud.get_owned(db, "categorias", user_id, categoria_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if subcategoria_id and not crud.get_owned(db, "subcategorias", user_id, subcategoria_id):
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")


def _check_categoria_despesa(db: Client, user_id: str, categoria_id: str) -> None:
    """Recorrente sempre confirma como despesa (ver confirmar()) — a
    categoria vinculada precisa ser do tipo 'despesa', mesma regra de
    _TIPO_CATEGORIA_ESPERADO em routers/transacoes.py."""
    categoria = db.table("categorias").select("tipo").eq("id", categoria_id).eq("user_id", user_id).execute()
    if categoria.data and categoria.data[0]["tipo"] != "despesa":
        raise HTTPException(status_code=422, detail="Categoria precisa ser do tipo 'despesa'")


@router.get("", response_model=list[LancamentoRecorrente])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id, order="descricao")


@router.get("/{recorrente_id}", response_model=LancamentoRecorrente)
def obter(recorrente_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, recorrente_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")


@router.post("", response_model=LancamentoRecorrente, status_code=201)
def criar(
    payload: LancamentoRecorrenteCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _check_refs(db, user_id, payload.conta_id, payload.categoria_id, payload.subcategoria_id)
    _check_categoria_despesa(db, user_id, payload.categoria_id)
    return crud.create(db, TABLE, user_id, payload.model_dump(mode="json"))


@router.patch("/{recorrente_id}", response_model=LancamentoRecorrente)
def atualizar(
    recorrente_id: str,
    payload: LancamentoRecorrenteUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        atual = crud.get_one(db, TABLE, user_id, recorrente_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")

    dados = payload.model_dump(mode="json", exclude_unset=True)
    _check_refs(
        db,
        user_id,
        dados.get("conta_id", atual["conta_id"]),
        dados.get("categoria_id", atual["categoria_id"]),
        dados.get("subcategoria_id", atual["subcategoria_id"]),
    )
    if "categoria_id" in dados:
        _check_categoria_despesa(db, user_id, dados["categoria_id"])

    try:
        return crud.update(db, TABLE, user_id, recorrente_id, dados)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")


@router.patch("/{recorrente_id}/ativo", response_model=LancamentoRecorrente)
def alternar_ativo(
    recorrente_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.set_ativo(db, TABLE, user_id, recorrente_id, ativo)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")


@router.delete("/{recorrente_id}", status_code=204)
def excluir(recorrente_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Apaga só o molde — meses já confirmados continuam existindo como
    transações reais normais (lancamento_recorrente_id vira null, ver
    schema.sql: on delete set null)."""
    result = db.table(TABLE).delete().eq("id", recorrente_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")


def _ja_confirmado(db: Client, user_id: str, recorrente_id: str, vigencia_mes: date, mes_fim: date) -> bool:
    return bool(
        db.table("transacoes")
        .select("id")
        .eq("user_id", user_id)
        .eq("lancamento_recorrente_id", recorrente_id)
        .gte("data_compra", vigencia_mes.isoformat())
        .lt("data_compra", mes_fim.isoformat())
        .execute()
        .data
    )


def _ja_pulado(db: Client, recorrente_id: str, vigencia_mes: date) -> bool:
    return bool(
        db.table("lancamentos_recorrentes_pulados")
        .select("id")
        .eq("lancamento_recorrente_id", recorrente_id)
        .eq("vigencia_mes", vigencia_mes.isoformat())
        .execute()
        .data
    )


@router.post("/{recorrente_id}/confirmar", response_model=Transacao, status_code=201)
def confirmar(
    recorrente_id: str,
    payload: VigenciaMesPayload,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Projeção virtual: nada existe em `transacoes` até este endpoint ser
    chamado pra um mês específico — cria a transação real (despesa) e
    vincula de volta ao recorrente (lancamento_recorrente_id)."""
    try:
        recorrente = crud.get_one(db, TABLE, user_id, recorrente_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")

    vigencia_mes = date(payload.vigencia_mes.year, payload.vigencia_mes.month, 1)
    mes_fim = somar_meses(vigencia_mes, 1)

    if _ja_confirmado(db, user_id, recorrente_id, vigencia_mes, mes_fim):
        raise HTTPException(status_code=409, detail="Este mês já foi confirmado para este lançamento recorrente")
    if _ja_pulado(db, recorrente_id, vigencia_mes):
        raise HTTPException(
            status_code=409,
            detail="Este mês foi marcado como pulado — desfaça o pular antes de confirmar",
        )

    data_compra = data_ocorrencia(vigencia_mes, recorrente["dia_mes"])

    row = {
        "user_id": user_id,
        "data_compra": data_compra.isoformat(),
        "valor": recorrente["valor"],
        "descricao": recorrente["descricao"],
        "tipo_movimento": "despesa",
        "pagamento": "avista",
        "parcela_atual": None,
        "parcela_total": None,
        "compra_parcelada_id": None,
        "conta_id": recorrente["conta_id"],
        "categoria_id": recorrente["categoria_id"],
        "subcategoria_id": recorrente["subcategoria_id"],
        "estrutura_custo": recorrente["estrutura_custo"],
        "caixinha_id": None,
        "meio_pagamento": recorrente["meio_pagamento"],
        "fatura_referencia": fatura_referencia_para(db, user_id, recorrente["conta_id"], data_compra),
        "fatura_override": False,
        "ajuste_de_transacao_id": None,
        "lancamento_recorrente_id": recorrente_id,
    }
    row["hash_dedup"] = compute_hash(
        user_id=user_id,
        data_compra=row["data_compra"],
        valor=row["valor"],
        descricao=row["descricao"],
        conta_id=row["conta_id"],
        tipo_movimento=row["tipo_movimento"],
        parcela_atual=None,
        parcela_total=None,
        compra_parcelada_id=None,
        # distingue de uma despesa manual idêntica lançada no mesmo dia —
        # sem isso, confirmar um mês colidiria com hash_dedup se o usuário
        # já tivesse lançado manualmente o mesmo valor/conta/descrição
        lancamento_recorrente_id=recorrente_id,
    )
    criada = inserir_transacao(db, row)
    sincronizar_item_orcamento(db, user_id, criada)
    return criada


@router.post("/{recorrente_id}/pular", response_model=MesPulado, status_code=201)
def pular(
    recorrente_id: str,
    payload: VigenciaMesPayload,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Marca um mês como "não aplicável" (ex: viajou, não teve a despesa
    naquele mês) — não cria nada em `transacoes`, só faz esse mês parar de
    aparecer como pendente em Compromissos Futuros e a busca avançar pro
    mês seguinte (ver services/recorrentes.proxima_ocorrencia_pendente)."""
    try:
        crud.get_one(db, TABLE, user_id, recorrente_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")

    vigencia_mes = date(payload.vigencia_mes.year, payload.vigencia_mes.month, 1)
    mes_fim = somar_meses(vigencia_mes, 1)

    if _ja_confirmado(db, user_id, recorrente_id, vigencia_mes, mes_fim):
        raise HTTPException(
            status_code=409, detail="Este mês já foi confirmado — exclua a transação antes de marcar como pulado"
        )
    if _ja_pulado(db, recorrente_id, vigencia_mes):
        raise HTTPException(status_code=409, detail="Este mês já foi marcado como pulado")

    result = (
        db.table("lancamentos_recorrentes_pulados")
        .insert({"lancamento_recorrente_id": recorrente_id, "vigencia_mes": vigencia_mes.isoformat()})
        .execute()
    )
    return result.data[0]


@router.delete("/{recorrente_id}/pular", status_code=204)
def desfazer_pular(
    recorrente_id: str,
    vigencia_mes: date,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Desfaz um "pular" — o mês volta a aparecer como pendente."""
    try:
        crud.get_one(db, TABLE, user_id, recorrente_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Lançamento recorrente não encontrado")

    mes_normalizado = date(vigencia_mes.year, vigencia_mes.month, 1)
    result = (
        db.table("lancamentos_recorrentes_pulados")
        .delete()
        .eq("lancamento_recorrente_id", recorrente_id)
        .eq("vigencia_mes", mes_normalizado.isoformat())
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Este mês não estava marcado como pulado")
