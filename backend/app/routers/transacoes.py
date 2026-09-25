from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.transacoes import (
    CompraParceladaCreate,
    EstruturaCusto,
    MeioPagamento,
    MoverFaturaPayload,
    ParcelaUpdate,
    ResumoLancamentos,
    Transacao,
    TransacaoCreate,
    TipoMovimento,
)
from ..services import crud
from ..services.dedup import compute_hash
from ..services.fatura import somar_meses
from ..services.orcamento_sync import sincronizar_item_orcamento
from ..services.resumo_financeiro import calcular_resumo
from ..services.transacao_insercao import fatura_referencia_para, inserir_transacao

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
    conta_id: str | None = None,
) -> None:
    """Caixinha é reserva, não investimento nem despesa — só faz sentido em
    aplicação/retirada. Categoria (quando informada) precisa ser do tipo
    compatível com o tipo de movimento (ver _TIPO_CATEGORIA_ESPERADO).
    Caixinha vinculada a uma conta "mora" nessa conta — o lançamento
    precisa usar a mesma conta, senão a reserva fica registrada num ledger
    diferente de onde o dinheiro realmente está."""
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
    if caixinha_id and conta_id:
        caixinha = db.table("caixinhas").select("conta_id").eq("id", caixinha_id).eq("user_id", user_id).execute()
        if caixinha.data and caixinha.data[0]["conta_id"] and caixinha.data[0]["conta_id"] != conta_id:
            raise HTTPException(
                status_code=422,
                detail="A conta do lançamento precisa ser a mesma conta vinculada à caixinha",
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
    # paginado: sem filtro de data (ex: limpar filtros em Lançamentos) já
    # passa de 1000 linhas numa conta real — ver buscar_todas_paginado
    return crud.buscar_todas_paginado(
        lambda: _query_filtrada(
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
        ).order("data_compra", desc=True)
    )


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
    dados = crud.buscar_todas_paginado(
        lambda: _query_filtrada(
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
    )
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
    _check_regras_tipo_movimento(
        db, user_id, payload.tipo_movimento, payload.categoria_id, payload.caixinha_id, payload.conta_id
    )
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
        fatura_referencia=fatura_referencia_para(db, user_id, payload.conta_id, payload.data_compra),
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
    criada = inserir_transacao(db, row)
    sincronizar_item_orcamento(db, user_id, criada)
    return criada


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
            "fatura_referencia": fatura_referencia_para(db, user_id, payload.conta_id, data_parcela),
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
        criada = inserir_transacao(db, row)
        sincronizar_item_orcamento(db, user_id, criada)
        criadas.append(criada)
    return criadas


@router.patch("/{transacao_id}", response_model=Transacao)
def atualizar(
    transacao_id: str,
    payload: TransacaoCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Edita um lançamento à vista. Parcela de compra parcelada não é
    editável por aqui — mexer numa parcela isolada quebraria a
    consistência do grupo (valor_total, hash por parcela); o caminho é
    excluir e lançar de novo. Se a fatura já foi movida manualmente
    (fatura_override), a edição preserva essa referência em vez de
    recalcular pelo dia de fechamento."""
    try:
        atual = crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    if atual["pagamento"] == "parcelado":
        raise HTTPException(
            status_code=422,
            detail=(
                "Parcela de compra parcelada não tem data/conta editáveis por aqui — use "
                "PATCH /transacoes/parceladas/{id} pra descrição/valor/categoria/subcategoria/"
                "estrutura de custo/meio de pagamento, ou exclua e lance novamente"
            ),
        )
    _check_refs(
        db, user_id, payload.conta_id, payload.categoria_id, payload.subcategoria_id,
        payload.caixinha_id, payload.ajuste_de_transacao_id,
    )
    _check_regras_tipo_movimento(
        db, user_id, payload.tipo_movimento, payload.categoria_id, payload.caixinha_id, payload.conta_id
    )
    _check_campos_obrigatorios(
        payload.tipo_movimento, payload.categoria_id, payload.estrutura_custo, payload.meio_pagamento,
        payload.caixinha_id,
    )
    row = payload.model_dump(mode="json")
    row.update(pagamento="avista", parcela_atual=None, parcela_total=None, compra_parcelada_id=None)
    if atual["fatura_override"]:
        row["fatura_referencia"] = atual["fatura_referencia"]
        row["fatura_override"] = True
    else:
        row["fatura_referencia"] = fatura_referencia_para(db, user_id, payload.conta_id, payload.data_compra)
        row["fatura_override"] = False
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
    try:
        atualizada = crud.update(db, TABLE, user_id, transacao_id, row)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    except Exception as exc:  # noqa: BLE001 — mesma tradução de unicidade usada em _insert
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Já existe um lançamento idêntico (mesma data, valor, conta e descrição).",
            ) from exc
        print(f"[transacoes] falha ao atualizar: {exc!r} — id={transacao_id}")
        raise HTTPException(status_code=500, detail="Falha ao salvar a transação") from exc
    sincronizar_item_orcamento(db, user_id, atualizada)
    return atualizada


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


@router.patch("/parceladas/{transacao_id}", response_model=Transacao)
def atualizar_parcela(
    transacao_id: str,
    payload: ParcelaUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Nível 1 da edição de compra parcelada (backlog), estendido na
    Rodada 21.1 pra incluir valor: edita descrição/valor/categoria/
    subcategoria/estrutura de custo/meio de pagamento de UMA parcela.
    Valor entra de propósito — não existe padrão bancário único pra
    distribuir centavos de arredondamento entre parcelas, então a fatura
    real do emissor pode diferir do que foi calculado na criação; editar
    mês a mês, conforme a fatura fecha, é a forma de manter o lançamento
    fiel à fatura real (ver ParcelaUpdate). Data e conta continuam
    travadas, exatamente como em PATCH /transacoes/{id}. Editar o grupo
    inteiro (recriar com novo valor total/quantidade de parcelas) fica
    pra decisão futura (nível 2, registrado no backlog como não
    priorizado)."""
    try:
        atual = crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    if atual["pagamento"] != "parcelado":
        raise HTTPException(
            status_code=422,
            detail="Este endpoint edita só parcelas — lançamento à vista usa PATCH /transacoes/{id}",
        )
    _check_refs(db, user_id, atual["conta_id"], payload.categoria_id, payload.subcategoria_id)
    _check_regras_tipo_movimento(db, user_id, "despesa", payload.categoria_id, None)
    _check_campos_obrigatorios("despesa", payload.categoria_id, payload.estrutura_custo, payload.meio_pagamento, None)
    row = payload.model_dump(mode="json")
    # descrição e valor entram no hash_dedup (unique) — precisa recalcular
    # pra não deixar o hash antigo estagnado, mesma lógica de atualizar() acima
    row["hash_dedup"] = compute_hash(
        user_id=user_id,
        data_compra=atual["data_compra"],
        valor=row["valor"],
        descricao=row["descricao"],
        conta_id=atual["conta_id"],
        tipo_movimento=atual["tipo_movimento"],
        parcela_atual=atual["parcela_atual"],
        parcela_total=atual["parcela_total"],
        compra_parcelada_id=atual["compra_parcelada_id"],
    )
    try:
        atualizada = crud.update(db, TABLE, user_id, transacao_id, row)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    except Exception as exc:  # noqa: BLE001 — mesma tradução de unicidade usada em atualizar()
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Já existe um lançamento idêntico (mesma data, valor, conta e descrição).",
            ) from exc
        raise HTTPException(status_code=500, detail="Falha ao salvar a parcela") from exc
    sincronizar_item_orcamento(db, user_id, atualizada)
    return atualizada


@router.delete("/parceladas/{compra_parcelada_id}", status_code=204)
def excluir_parcelada(
    compra_parcelada_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)
):
    """Nível 3 da edição de compra parcelada (backlog): exclui todas as
    parcelas do grupo numa ação só, em vez de repetir DELETE /transacoes/
    {id} uma vez por parcela. Cobre metade da dor do nível 2 (recriar o
    grupo com novos parâmetros) sem o risco de inconsistência — cancela e
    permite relançar do zero."""
    result = (
        db.table(TABLE).delete().eq("compra_parcelada_id", compra_parcelada_id).eq("user_id", user_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Compra parcelada não encontrada")
    db.table("compras_parceladas").delete().eq("id", compra_parcelada_id).eq("user_id", user_id).execute()


@router.delete("/{transacao_id}", status_code=204)
def excluir(transacao_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = db.table(TABLE).delete().eq("id", transacao_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
