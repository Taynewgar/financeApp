from datetime import date, timedelta
from typing import Literal

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
    RetiradaPendentePayload,
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
_JANELA_DESCRICAO_DIAS = 180  # ~6 meses — mesma janela de categorias/subcategorias mais-usadas


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
    pagamento: Literal["avista", "parcelado"] | None,
    data_inicio: date | None,
    data_fim: date | None,
    descricao: str | None,
):
    """Monta a query de busca/filtro usada tanto pela listagem quanto pelo
    resumo — os mesmos filtros da aba "Busca de Lançamentos" do app
    original (categoria, subcategoria, conta, caixinha, tipo de movimento,
    estrutura de custo, meio de pagamento, à vista/parcelado, período e
    texto na descrição)."""
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
    if pagamento:
        query = query.eq("pagamento", pagamento)
    if data_inicio:
        query = query.gte("data_compra", data_inicio.isoformat())
    if data_fim:
        query = query.lte("data_compra", data_fim.isoformat())
    if descricao:
        # cada palavra digitada vira um filtro ilike próprio (AND entre
        # eles) — a descrição só precisa conter todas as palavras, em
        # qualquer ordem, em vez de exigir a frase inteira como substring
        # contígua
        for termo in descricao.split():
            query = query.ilike("descricao", f"%{termo}%")
    return query


def _check_refs(
    db: Client,
    user_id: str,
    conta_id: str,
    categoria_id: str | None = None,
    subcategoria_id: str | None = None,
    caixinha_id: str | None = None,
    ajuste_de_transacao_id: str | None = None,
    caixinha_origem_id: str | None = None,
    despesa_origem_retirada_id: str | None = None,
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
    if caixinha_origem_id and not crud.get_owned(db, "caixinhas", user_id, caixinha_origem_id):
        raise HTTPException(status_code=404, detail="Caixinha de origem não encontrada")
    if despesa_origem_retirada_id and not crud.get_owned(db, TABLE, user_id, despesa_origem_retirada_id):
        raise HTTPException(status_code=404, detail="Despesa de origem da retirada não encontrada")


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
    caixinha_origem_id: str | None = None,
    despesa_origem_retirada_id: str | None = None,
) -> None:
    """Caixinha é reserva, não investimento nem despesa — só faz sentido em
    aplicação/retirada. Categoria (quando informada) precisa ser do tipo
    compatível com o tipo de movimento (ver _TIPO_CATEGORIA_ESPERADO).
    Caixinha vinculada a uma conta "mora" nessa conta — o lançamento
    precisa usar a mesma conta, senão a reserva fica registrada num ledger
    diferente de onde o dinheiro realmente está. caixinha_origem_id (item
    58) é o oposto de caixinha_id: só faz sentido em DESPESA — é a marca
    de "isso já tava guardado", não uma movimentação de reserva em si.
    despesa_origem_retirada_id (item 58) é o inverso: só faz sentido numa
    RETIRADA — é o rastro pra reabrir o lembrete da despesa se essa
    retirada for excluída."""
    if caixinha_origem_id and tipo_movimento != "despesa":
        raise HTTPException(
            status_code=422,
            detail="Vínculo com caixinha de origem só se aplica a lançamentos de despesa",
        )
    if despesa_origem_retirada_id and tipo_movimento != "retirada":
        raise HTTPException(
            status_code=422,
            detail="Vínculo com despesa de origem só se aplica a lançamentos de retirada",
        )
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
    pagamento: Literal["avista", "parcelado"] | None = None,
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
            pagamento,
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
    pagamento: Literal["avista", "parcelado"] | None = None,
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
            pagamento,
            data_inicio,
            data_fim,
            descricao,
        )
    )
    resultado = calcular_resumo(dados)
    resultado.pop("_receita_ajustada")
    resultado["total_lancamentos"] = len(dados)
    return resultado


# precisa vir antes de GET /{transacao_id} — mesmo motivo de /resumo acima
@router.get("/descricoes-mais-usadas", response_model=list[str])
def descricoes_mais_usadas(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    categoria_id: str | None = None,
    subcategoria_id: str | None = None,
    caixinha_id: str | None = None,
    limite: int = 5,
):
    """Ranking de descrições (texto literal, sem normalizar) por frequência
    de uso nos últimos ~6 meses — mesmo padrão de /categorias/mais-usadas e
    /subcategorias/mais-usadas, aqui por descrição em vez de id. Usado no
    Novo Lançamento tanto pros chips de atalho quanto pela checagem de
    quase-duplicata (que recebe uma janela maior e compara as próprias).
    `caixinha_id` cobre reserva (aplicação/retirada), que não usa
    categoria/subcategoria — as 2 situações não se misturam na prática
    (uma transação real tem um ou outro, nunca os dois)."""
    if not categoria_id and not subcategoria_id and not caixinha_id:
        return []

    desde = (date.today() - timedelta(days=_JANELA_DESCRICAO_DIAS)).isoformat()
    query = db.table(TABLE).select("descricao").eq("user_id", user_id).gte("data_compra", desde)
    if subcategoria_id:
        query = query.eq("subcategoria_id", subcategoria_id)
    elif categoria_id:
        query = query.eq("categoria_id", categoria_id)
    else:
        query = query.eq("caixinha_id", caixinha_id)

    transacoes = crud.buscar_todas_paginado(lambda: query)
    contagem: dict[str, int] = {}
    for t in transacoes:
        descricao = (t["descricao"] or "").strip()
        if descricao:
            contagem[descricao] = contagem.get(descricao, 0) + 1

    ranking = sorted(contagem.items(), key=lambda item: (-item[1], item[0]))
    return [descricao for descricao, _contagem in ranking[:limite]]


# precisa vir antes de GET /{transacao_id} — mesmo motivo de /resumo acima
@router.get("/ultimos-por-conta", response_model=dict[str, list[Transacao]])
def ultimos_por_conta(
    limite: int = 10,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Últimos `limite` lançamentos RAIZ de cada conta do usuário — à
    vista, ou só a 1ª parcela de uma compra parcelada (nunca cada parcela
    individual). Helper pra ver rápido onde parou de lançar numa conta,
    sem listar o ruído de N parcelas futuras da mesma compra (item 54 do
    backlog) — usado pela seção "Últimos lançamentos por conta" em
    Lançamentos."""
    contas = crud.list_all(db, "contas", user_id)
    resultado: dict[str, list[Transacao]] = {}
    for conta in contas:
        linhas = (
            db.table(TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("conta_id", conta["id"])
            .or_("pagamento.eq.avista,parcela_atual.eq.1")
            .order("data_compra", desc=True)
            .limit(limite)
            .execute()
        ).data
        resultado[conta["id"]] = linhas
    return resultado


@router.get("/retiradas-pendentes", response_model=list[Transacao])
def retiradas_pendentes(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Despesas marcadas como já cobertas por uma caixinha (item 58) que
    ainda aguardam o saque real — alimenta o card "Retiradas pendentes de
    caixinha" no Dashboard. Precisa vir antes de GET /{transacao_id},
    mesmo motivo de /resumo acima."""
    return crud.buscar_todas_paginado(
        lambda: db.table(TABLE)
        .select("*")
        .eq("user_id", user_id)
        .eq("retirada_pendente", True)
        .order("data_compra", desc=True)
    )


@router.get("/{transacao_id}", response_model=Transacao)
def obter(transacao_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")


# hash_dedup existe pra pegar double-submit acidental (ex: duplo clique),
# mas com só esses 5 campos também bloqueia 2 transações reais e
# diferentes que coincidem em data/valor/descrição/conta/tipo (ex: 2
# assinaturas iguais cobradas no mesmo dia) — achado 2026-09-25 migrando
# dados reais, ver `agrupar_por_chave_hash`/`gravar_avista_duplicado` em
# scripts/migrar_dados_antigos.py. Mesma técnica aqui: quando o usuário
# confirma que é um lançamento real (forcar_duplicado), soma um índice
# de ocorrência só ao cálculo do hash — nunca gravado na linha — até
# achar uma combinação livre. Sem forçar, o comportamento de hoje não
# muda: ocorrência 0 usa a MESMA fórmula de sempre (sem a chave extra).
_MAX_OCORRENCIAS_DUPLICADO = 20


def _com_desambiguacao_de_duplicata(tentar, row: dict, campos_hash: dict, forcar_duplicado: bool) -> dict:
    """`tentar` é a operação (inserir OU atualizar) que lê `row["hash_dedup"]`
    no momento em que roda — generaliza a técnica pros 2 pontos que
    recalculam hash_dedup num lançamento avista (criar/atualizar)."""
    row["hash_dedup"] = compute_hash(**campos_hash)
    try:
        return tentar()
    except HTTPException as exc:
        if exc.status_code != 409 or not forcar_duplicado:
            raise
        for ocorrencia in range(1, _MAX_OCORRENCIAS_DUPLICADO):
            row["hash_dedup"] = compute_hash(**campos_hash, ocorrencia=ocorrencia)
            try:
                return tentar()
            except HTTPException as exc_ocorrencia:
                if exc_ocorrencia.status_code != 409:
                    raise
        raise


def _atualizar_avista(db: Client, user_id: str, transacao_id: str, row: dict) -> dict:
    try:
        return crud.update(db, TABLE, user_id, transacao_id, row)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    except Exception as exc:  # noqa: BLE001 — mesma tradução de unicidade usada em inserir_transacao
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Já existe um lançamento idêntico (mesma data, valor, conta e descrição).",
            ) from exc
        print(f"[transacoes] falha ao atualizar: {exc!r} — id={transacao_id}")
        raise HTTPException(status_code=500, detail="Falha ao salvar a transação") from exc


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
        payload.caixinha_origem_id,
        payload.despesa_origem_retirada_id,
    )
    _check_regras_tipo_movimento(
        db, user_id, payload.tipo_movimento, payload.categoria_id, payload.caixinha_id, payload.conta_id,
        payload.caixinha_origem_id, payload.despesa_origem_retirada_id,
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
        # item 58: nasce pendente sempre que vinculada a uma caixinha de
        # origem — nunca setável direto pelo cliente na criação
        retirada_pendente=bool(payload.caixinha_origem_id),
    )
    campos_hash = dict(
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
    criada = _com_desambiguacao_de_duplicata(
        lambda: inserir_transacao(db, row), row, campos_hash, payload.forcar_duplicado
    )
    sincronizar_item_orcamento(db, user_id, criada)
    return criada


def _existe_compra_parcelada_igual(db: Client, user_id: str, payload: CompraParceladaCreate) -> bool:
    """hash_dedup de cada parcela inclui compra_parcelada_id — gerado
    novo a cada chamada, então nunca detecta double-submit aqui (achado
    2026-10-02, item 68). Checagem em nível de aplicação, ANTES de criar
    o grupo (evita header fantasma em compras_parceladas quando bloqueia):
    acha a 1ª parcela (sempre existe) com a mesma descrição/data/conta,
    depois confirma valor_total/parcela_total no cabeçalho do grupo dela.
    Não é uma constraint de banco (sem coluna nova em compras_parceladas,
    que não guarda conta/data) — suficiente pra pegar double-submit real
    (mesmo clique, mesmo payload), não uma garantia de unicidade total."""
    primeiras_parcelas = (
        db.table(TABLE)
        .select("compra_parcelada_id")
        .eq("user_id", user_id)
        .eq("parcela_atual", 1)
        .eq("data_compra", payload.data_primeira_parcela.isoformat())
        .eq("conta_id", payload.conta_id)
        .eq("descricao", payload.descricao)
        .execute()
        .data
    )
    ids_candidatos = [p["compra_parcelada_id"] for p in primeiras_parcelas if p.get("compra_parcelada_id")]
    if not ids_candidatos:
        return False
    grupos = db.table("compras_parceladas").select("valor_total,parcela_total").in_("id", ids_candidatos).execute().data
    return any(g["valor_total"] == payload.valor_total and g["parcela_total"] == payload.parcela_total for g in grupos)


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
    if not payload.forcar_duplicado and _existe_compra_parcelada_igual(db, user_id, payload):
        raise HTTPException(
            status_code=409,
            detail="Já existe uma compra parcelada idêntica (mesma descrição, valor total, nº de parcelas, "
            "data da 1ª parcela e conta).",
        )

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
        payload.caixinha_id, payload.ajuste_de_transacao_id, payload.caixinha_origem_id,
        payload.despesa_origem_retirada_id,
    )
    _check_regras_tipo_movimento(
        db, user_id, payload.tipo_movimento, payload.categoria_id, payload.caixinha_id, payload.conta_id,
        payload.caixinha_origem_id, payload.despesa_origem_retirada_id,
    )
    _check_campos_obrigatorios(
        payload.tipo_movimento, payload.categoria_id, payload.estrutura_custo, payload.meio_pagamento,
        payload.caixinha_id,
    )
    row = payload.model_dump(mode="json")
    row.update(pagamento="avista", parcela_atual=None, parcela_total=None, compra_parcelada_id=None)
    # item 58: só reseta o lembrete quando o VÍNCULO muda (nasce, muda de
    # caixinha, ou é removido) — uma edição que não mexe nisso (ex: só
    # corrigir a descrição) não pode reabrir um lembrete que o usuário já
    # tinha resolvido manualmente.
    if payload.caixinha_origem_id != atual.get("caixinha_origem_id"):
        row["retirada_pendente"] = bool(payload.caixinha_origem_id)
    else:
        row["retirada_pendente"] = atual.get("retirada_pendente", False)
    if atual["fatura_override"]:
        row["fatura_referencia"] = atual["fatura_referencia"]
        row["fatura_override"] = True
    else:
        row["fatura_referencia"] = fatura_referencia_para(db, user_id, payload.conta_id, payload.data_compra)
        row["fatura_override"] = False
    campos_hash = dict(
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
    atualizada = _com_desambiguacao_de_duplicata(
        lambda: _atualizar_avista(db, user_id, transacao_id, row), row, campos_hash, payload.forcar_duplicado
    )
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


@router.patch("/{transacao_id}/retirada-pendente", response_model=Transacao)
def atualizar_retirada_pendente(
    transacao_id: str,
    payload: RetiradaPendentePayload,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Item 58: ação rápida do card "Retiradas pendentes de caixinha" no
    Dashboard — liga/desliga só o lembrete, sem reenviar a despesa
    inteira. Usada tanto por "Já retirei, só marcar" (pendente=false
    direto) quanto, pelo frontend, depois de "Lançar retirada agora"
    criar a transação de retirada de verdade."""
    try:
        atual = crud.get_one(db, TABLE, user_id, transacao_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    if not atual.get("caixinha_origem_id"):
        raise HTTPException(status_code=422, detail="Esta transação não tem caixinha de origem vinculada")
    try:
        return crud.update(db, TABLE, user_id, transacao_id, {"retirada_pendente": payload.pendente})
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


def _reabrir_retirada_pendente_se_aplicavel(db: Client, user_id: str, despesa_id: str) -> None:
    """Item 58: excluir a transação de retirada que resolveu uma despesa
    devolve o lembrete pra "pendente" — sem isso, a despesa fica
    permanentemente marcada como resolvida mesmo sem a retirada real ter
    ficado registrada. Só reabre se a despesa ainda tiver vínculo com
    caixinha de origem (se o usuário removeu o vínculo manualmente nesse
    meio tempo, não há o que reabrir); ignora silenciosamente se a
    despesa já não existir mais (despesa_origem_retirada_id vira null
    sozinho via "on delete set null" nesse caso, mas a exclusão da
    despesa pode ter vindo antes da da retirada)."""
    try:
        despesa = crud.get_one(db, TABLE, user_id, despesa_id)
    except crud.NotFound:
        return
    if despesa.get("caixinha_origem_id"):
        crud.update(db, TABLE, user_id, despesa_id, {"retirada_pendente": True})


@router.delete("/{transacao_id}", status_code=204)
def excluir(transacao_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = db.table(TABLE).delete().eq("id", transacao_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    despesa_origem_id = result.data[0].get("despesa_origem_retirada_id")
    if despesa_origem_id:
        _reabrir_retirada_pendente_se_aplicavel(db, user_id, despesa_origem_id)
