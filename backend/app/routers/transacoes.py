from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.transacoes import (
    CompraParceladaCreate,
    EstruturaCusto,
    MeioPagamento,
    MoverFaturaPayload,
    ResumoLancamentos,
    Transacao,
    TransacaoCreate,
    TipoMovimento,
)
from ..services import crud
from ..services.dedup import compute_hash
from ..services.fatura import calcular_fatura_referencia, somar_meses
from ..services.resumo_financeiro import calcular_resumo

router = APIRouter(prefix="/transacoes", tags=["transacoes"])
TABLE = "transacoes"


def _query_filtrada(
    db: Client,
    user_id: str,
    categoria_id: str | None,
    subcategoria_id: str | None,
    conta_id: str | None,
    caixinha_id: str | None,
    tipo_movimento: TipoMovimento | None,
    estrutura_custo: EstruturaCusto | None,
    meio_pagamento: MeioPagamento | None,
    data_inicio: date | None,
    data_fim: date | None,
    descricao: str | None,
):
    """Monta a query de busca/filtro usada tanto pela listagem quanto pelo
    resumo — os mesmos filtros da aba "Busca de Lançamentos" do app
    original (categoria, subcategoria, conta, caixinha, tipo de movimento,
    estrutura de custo, meio de pagamento, período e texto na descrição)."""
    query = db.table(TABLE).select("*").eq("user_id", user_id)
    if categoria_id:
        query = query.eq("categoria_id", categoria_id)
    if subcategoria_id:
        query = query.eq("subcategoria_id", subcategoria_id)
    if conta_id:
        query = query.eq("conta_id", conta_id)
    if caixinha_id:
        query = query.eq("caixinha_id", caixinha_id)
    if tipo_movimento:
        query = query.eq("tipo_movimento", tipo_movimento)
    if estrutura_custo:
        query = query.eq("estrutura_custo", estrutura_custo)
    if meio_pagamento:
        query = query.eq("meio_pagamento", meio_pagamento)
    if data_inicio:
        query = query.gte("data_compra", data_inicio.isoformat())
    if data_fim:
        query = query.lte("data_compra", data_fim.isoformat())
    if descricao:
        query = query.ilike("descricao", f"%{descricao}%")
    return query


def _check_refs(
    db: Client,
    user_id: str,
    conta_id: str,
    categoria_id: str | None = None,
    subcategoria_id: str | None = None,
    caixinha_id: str | None = None,
    ajuste_de_transacao_id: str | None = None,
) -> None:
    if not crud.get_owned(db, "contas", user_id, conta_id):
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    if categoria_id and not crud.get_owned(db, "categorias", user_id, categoria_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if subcategoria_id and not crud.get_owned(db, "subcategorias", user_id, subcategoria_id):
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    if caixinha_id and not crud.get_owned(db, "caixinhas", user_id, caixinha_id):
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
    if ajuste_de_transacao_id and not crud.get_owned(db, TABLE, user_id, ajuste_de_transacao_id):
        raise HTTPException(status_code=404, detail="Transação de ajuste referenciada não encontrada")


# receita usa a categoria "pai" tipo receita, despesa/estorno/ressarcimento
# usam categoria tipo despesa, aplicação/retirada (investimento) usam
# categoria tipo investimento — ver TipoCategoria em schemas/categorias.py
_TIPO_CATEGORIA_ESPERADO = {
    "receita": "receita",
    "despesa": "despesa",
    "estorno": "despesa",
    "ressarcimento": "despesa",
    "aplicacao": "investimento",
    "retirada": "investimento",
}


def _check_regras_tipo_movimento(
    db: Client,
    user_id: str,
    tipo_movimento: str,
    categoria_id: str | None,
    caixinha_id: str | None,
) -> None:
    """Caixinha é reserva, não investimento nem despesa — só faz sentido em
    aplicação/retirada. Categoria (quando informada) precisa ser do tipo
    compatível com o tipo de movimento (ver _TIPO_CATEGORIA_ESPERADO)."""
    if categoria_id:
        categoria = db.table("categorias").select("tipo").eq("id", categoria_id).eq("user_id", user_id).execute()
        if categoria.data:
            esperado = _TIPO_CATEGORIA_ESPERADO[tipo_movimento]
            if categoria.data[0]["tipo"] != esperado:
                raise HTTPException(
                    status_code=422,
                    detail=f"Categoria precisa ser do tipo '{esperado}' para esse tipo de lançamento",
                )
    if caixinha_id and tipo_movimento not in ("aplicacao", "retirada"):
        raise HTTPException(
            status_code=422,
            detail="Caixinha (reserva) só pode ser usada em lançamentos de aplicação/retirada",
        )


def _check_campos_obrigatorios(
    tipo_movimento: str,
    categoria_id: str | None,
    estrutura_custo: str | None,
    meio_pagamento: str | None,
    caixinha_id: str | None,
) -> None:
    """Despesa exige classificação completa — sem categoria/estrutura de
    custo/meio de pagamento a Estrutura de Custo e a Busca perdem precisão.
    Investimento (aplicação/retirada sem caixinha) sempre exige estrutura
    de custo; reserva (com caixinha) não usa nenhum desses campos."""
    faltando = []
    if tipo_movimento == "despesa":
        if not categoria_id:
            faltando.append("categoria_id")
        if not estrutura_custo:
            faltando.append("estrutura_custo")
        if not meio_pagamento:
            faltando.append("meio_pagamento")
    elif tipo_movimento in ("aplicacao", "retirada") and not caixinha_id and not estrutura_custo:
        faltando.append("estrutura_custo")
    if faltando:
        raise HTTPException(status_code=422, detail=f"Campo(s) obrigatório(s) faltando: {', '.join(faltando)}")


def _fatura_referencia_para(db: Client, user_id: str, conta_id: str, data_compra) -> str | None:
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


def _insert(db: Client, row: dict) -> dict:
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


@router.get("", response_model=list[Transacao])
def listar(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    categoria_id: str | None = None,
    subcategoria_id: str | None = None,
    conta_id: str | None = None,
    caixinha_id: str | None = None,
    tipo_movimento: TipoMovimento | None = None,
    estrutura_custo: EstruturaCusto | None = None,
    meio_pagamento: MeioPagamento | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    descricao: str | None = None,
):
    query = _query_filtrada(
        db,
        user_id,
        categoria_id,
        subcategoria_id,
        conta_id,
        caixinha_id,
        tipo_movimento,
        estrutura_custo,
        meio_pagamento,
        data_inicio,
        data_fim,
        descricao,
    )
    return query.order("data_compra", desc=True).execute().data


# precisa vir antes de GET /{transacao_id} — senão "/transacoes/resumo"
# seria interpretado como transacao_id="resumo" pelo roteamento
@router.get("/resumo", response_model=ResumoLancamentos)
def resumo(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    categoria_id: str | None = None,
    subcategoria_id: str | None = None,
    conta_id: str | None = None,
    caixinha_id: str | None = None,
    tipo_movimento: TipoMovimento | None = None,
    estrutura_custo: EstruturaCusto | None = None,
    meio_pagamento: MeioPagamento | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    descricao: str | None = None,
):
    """Os mesmos cartões de resumo da aba Busca de Lançamentos do app
    original, calculados sobre exatamente o mesmo conjunto de lançamentos
    que os filtros acima retornariam."""
    query = _query_filtrada(
        db,
        user_id,
        categoria_id,
        subcategoria_id,
        conta_id,
        caixinha_id,
        tipo_movimento,
        estrutura_custo,
        meio_pagamento,
        data_inicio,
        data_fim,
        descricao,
    )
    dados = query.execute().data
    resultado = calcular_resumo(dados)
    resultado.pop("_receita_ajustada")
    resultado["total_lancamentos"] = len(dados)
    return resultado


@router.get("/{transacao_id}", response_model=Transacao)
def obter(transacao_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")


@router.post("", response_model=Transacao, status_code=201)
def criar(payload: TransacaoCreate, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    _check_refs(
        db,
        user_id,
        payload.conta_id,
        payload.categoria_id,
        payload.subcategoria_id,
        payload.caixinha_id,
        payload.ajuste_de_transacao_id,
    )
    _check_regras_tipo_movimento(db, user_id, payload.tipo_movimento, payload.categoria_id, payload.caixinha_id)
    _check_campos_obrigatorios(
        payload.tipo_movimento, payload.categoria_id, payload.estrutura_custo, payload.meio_pagamento,
        payload.caixinha_id,
    )
    row = payload.model_dump(mode="json")
    row.update(
        user_id=user_id,
        pagamento="avista",
        parcela_atual=None,
        parcela_total=None,
        compra_parcelada_id=None,
        fatura_referencia=_fatura_referencia_para(db, user_id, payload.conta_id, payload.data_compra),
        fatura_override=False,
    )
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
    )
    return _insert(db, row)


@router.post("/parceladas", response_model=list[Transacao], status_code=201)
def criar_parcelada(
    payload: CompraParceladaCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Materializa uma parcela por ciclo, como já aparece na fatura real do
    cartão — em vez de projetar parcelas futuras só na hora do relatório."""
    _check_refs(db, user_id, payload.conta_id, payload.categoria_id, payload.subcategoria_id)
    _check_regras_tipo_movimento(db, user_id, "despesa", payload.categoria_id, None)
    _check_campos_obrigatorios("despesa", payload.categoria_id, payload.estrutura_custo, payload.meio_pagamento, None)

    grupo = (
        db.table("compras_parceladas")
        .insert(
            {
                "user_id": user_id,
                "descricao": payload.descricao,
                "valor_total": payload.valor_total,
                "parcela_total": payload.parcela_total,
            }
        )
        .execute()
        .data[0]
    )

    valor_parcela = round(payload.valor_total / payload.parcela_total, 2)
    diferenca_arredondamento = round(payload.valor_total - valor_parcela * payload.parcela_total, 2)

    criadas = []
    for i in range(payload.parcela_total):
        data_parcela = somar_meses(payload.data_primeira_parcela, i)
        ultima_parcela = i == payload.parcela_total - 1
        valor = valor_parcela + (diferenca_arredondamento if ultima_parcela else 0)

        row = {
            "user_id": user_id,
            "data_compra": data_parcela.isoformat(),
            "valor": valor,
            "descricao": payload.descricao,
            "tipo_movimento": "despesa",
            "pagamento": "parcelado",
            "parcela_atual": i + 1,
            "parcela_total": payload.parcela_total,
            "compra_parcelada_id": grupo["id"],
            "conta_id": payload.conta_id,
            "categoria_id": payload.categoria_id,
            "subcategoria_id": payload.subcategoria_id,
            "estrutura_custo": payload.estrutura_custo,
            "meio_pagamento": payload.meio_pagamento,
            "fatura_referencia": _fatura_referencia_para(db, user_id, payload.conta_id, data_parcela),
            "fatura_override": False,
        }
        row["hash_dedup"] = compute_hash(
            user_id=user_id,
            data_compra=row["data_compra"],
            valor=row["valor"],
            descricao=row["descricao"],
            conta_id=row["conta_id"],
            tipo_movimento=row["tipo_movimento"],
            parcela_atual=row["parcela_atual"],
            parcela_total=row["parcela_total"],
            compra_parcelada_id=row["compra_parcelada_id"],
        )
        criadas.append(_insert(db, row))
    return criadas


@router.patch("/{transacao_id}/fatura", response_model=Transacao)
def mover_fatura(
    transacao_id: str,
    payload: MoverFaturaPayload,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Escape hatch para quando o banco lança a compra num ciclo diferente
    do calculado (liquidação atrasada pelo lojista/adquirente) — move só a
    referência de fatura, nunca a data real da compra. Só existe fatura
    (ciclo de fechamento) pra conta do tipo cartão de crédito — mover fatura
    de qualquer outro tipo de conta não tem o que mover."""
    try:
        transacao = crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    conta = crud.get_one(db, "contas", user_id, transacao["conta_id"])
    if conta["tipo_conta"] != "cartao_credito":
        raise HTTPException(
            status_code=422,
            detail="Só é possível mover fatura de uma transação em conta do tipo cartão de crédito",
        )
    try:
        return crud.update(
            db,
            TABLE,
            user_id,
            transacao_id,
            {"fatura_referencia": payload.fatura_referencia.isoformat(), "fatura_override": True},
        )
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")


@router.delete("/{transacao_id}", status_code=204)
def excluir(transacao_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = db.table(TABLE).delete().eq("id", transacao_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
