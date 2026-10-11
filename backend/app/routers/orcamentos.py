from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.orcamentos import (
    Orcamento,
    OrcamentoCreate,
    OrcamentoItem,
    OrcamentoItemCreate,
    OrcamentoItemUpdate,
    OrcamentoUpdate,
)
from ..services import crud
from ..services.fatura import somar_meses
from ..services.orcamento_saldo import calcular_realizado_item_em_lote, carregar_dados_periodo, saldo_anterior_em_lote
from ..services.orcamento_sync import classificar_transacao_para_orcamento
from ..services.orcamento_teto import calcular_teto_bucket

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])
TABLE = "orcamentos"
ITENS_TABLE = "orcamento_itens"


def _carregar_contexto_saldo(db: Client, user_id: str, orcamento: dict) -> tuple[dict, dict, dict, dict]:
    """Carrega em lote (3 SELECTs fixos) tudo que `saldo_anterior_em_lote`
    precisa pra recalcular a cadeia de saldo_anterior de qualquer item do
    orçamento informado, mais um cache novo — 1 chamada por requisição,
    reaproveitada por todo item que essa requisição precisar enriquecer/
    validar (ver `carregar_dados_periodo`, services/orcamento_saldo.py).
    Substituiu `saldo_anterior_ao_vivo()` aqui em 2026-09-25 (item 24 do
    backlog, mesma classe de bug já corrigida em Estrutura de Custo, Rodada
    27): cada item pedia sua própria cadeia de meses anteriores direto no
    banco — uma lista de N itens virava até N cadeias de idas e voltas
    sequenciais ao Supabase, todas repetindo o mesmo histórico de
    orçamentos/transações."""
    vigencia_mes = date.fromisoformat(orcamento["vigencia_mes"])
    orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes = carregar_dados_periodo(
        db, user_id, vigencia_mes, vigencia_mes
    )
    return orcamento_por_mes, itens_por_orcamento_id, transacoes_por_mes, {}


def _enriquecer_item(item: dict, orcamento: dict, contexto_saldo: tuple[dict, dict, dict, dict]) -> dict:
    """Acrescenta os campos calculados (nunca gravados) que dependem do
    orçamento-pai: saldo_anterior recalculado ao vivo (ver
    services/orcamento_saldo.py — a coluna gravada fica congelada desde o
    último "gerar próximo mês"), disponivel (envelope acumulado) e as duas
    leituras de percentual (sobre a renda total e sobre o teto do bucket).
    `contexto_saldo` vem de `_carregar_contexto_saldo` — 100% em memória
    daqui pra baixo, sem nenhuma consulta ao banco."""
    vigencia_mes = date.fromisoformat(orcamento["vigencia_mes"])
    saldo_anterior = saldo_anterior_em_lote(item, vigencia_mes, *contexto_saldo)
    disponivel = round(item["orcamento_mensal"] + saldo_anterior, 2)
    receita_base = orcamento["receita_base"]
    teto_bucket = calcular_teto_bucket(orcamento, item["bucket"])
    return {
        **item,
        "saldo_anterior": saldo_anterior,
        "disponivel": disponivel,
        "percentual_da_renda": round(item["orcamento_mensal"] / receita_base * 100, 2) if receita_base else 0.0,
        "percentual_do_teto": round(item["orcamento_mensal"] / teto_bucket * 100, 2) if teto_bucket else 0.0,
    }




def _popular_itens_de_transacoes_existentes(db: Client, user_id: str, orcamento: dict) -> None:
    """Ao criar (ou gerar via "próximo mês") um orçamento pro mês que já
    tem lançamentos — comum lançar antes de planejar —, cria os itens com
    orcamento_mensal=0 pra cada categoria/subcategoria já lançada nesse
    mês. Mesma regra de paridade que sincronizar_item_orcamento já aplica
    de forma reativa daqui pra frente (nova transação chegando); isto aqui
    cobre o retroativo (transação que já existia antes do orçamento).

    Em lote — 2 buscas fixas + no máximo 1 insert, nunca 1 ida e volta por
    transação: chamar `sincronizar_item_orcamento` (que já teria feito 2-3
    buscas próprias, incluindo reencontrar o orçamento que aqui já temos em
    mãos) uma vez por transação do mês deixava "Gerar orçamento"/"Criar do
    zero" visivelmente travados numa conta real (centenas de transações no
    mês, achado 2026-09-30 — usuário reportou que o fix da Rodada 38, que só
    cobriu o `calcular_realizado_item_em_lote` deste mesmo endpoint, não
    resolveu a lentidão; esta era a segunda N+1 do mesmo fluxo)."""
    mes_inicio = date.fromisoformat(orcamento["vigencia_mes"])
    mes_fim = somar_meses(mes_inicio, 1)
    transacoes = (
        db.table("transacoes")
        .select("tipo_movimento,caixinha_id,estrutura_custo,categoria_id,subcategoria_id,data_compra")
        .eq("user_id", user_id)
        .gte("data_compra", mes_inicio.isoformat())
        .lt("data_compra", mes_fim.isoformat())
        .execute()
        .data
    )
    if not transacoes:
        return

    itens_existentes = (
        db.table(ITENS_TABLE).select("categoria_id,subcategoria_id").eq("orcamento_id", orcamento["id"]).execute().data
    )
    chaves_existentes = {
        (i["subcategoria_id"], None) if i.get("subcategoria_id") else (None, i.get("categoria_id"))
        for i in itens_existentes
    }

    chaves_novas: set[tuple[str | None, str | None]] = set()
    novos_itens = []
    for transacao in transacoes:
        classificacao = classificar_transacao_para_orcamento(transacao)
        if classificacao is None:
            continue
        bucket, subcategoria_id, categoria_id = classificacao
        chave = (subcategoria_id, None) if subcategoria_id else (None, categoria_id)
        if chave in chaves_existentes or chave in chaves_novas:
            continue
        chaves_novas.add(chave)
        novos_itens.append(
            {
                "orcamento_id": orcamento["id"],
                "bucket": bucket,
                "categoria_id": None if subcategoria_id else categoria_id,
                "subcategoria_id": subcategoria_id,
                "orcamento_mensal": 0,
            }
        )

    if novos_itens:
        db.table(ITENS_TABLE).insert(novos_itens).execute()


def _get_orcamento_ou_404(db: Client, user_id: str, orcamento_id: str) -> dict:
    try:
        return crud.get_one(db, TABLE, user_id, orcamento_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")


def _get_item_ou_404(db: Client, orcamento_id: str, item_id: str) -> dict:
    # orcamento_itens não tem coluna user_id (o RLS confere posse via join
    # com orcamentos) — por isso a checagem aqui é sempre orcamento_id +
    # id, nunca user_id direto.
    result = db.table(ITENS_TABLE).select("*").eq("id", item_id).eq("orcamento_id", orcamento_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Item de orçamento não encontrado")
    return result.data[0]


def _check_refs_item(
    db: Client,
    user_id: str,
    categoria_id: str | None,
    subcategoria_id: str | None,
    conta_vinculada_id: str | None,
) -> None:
    if categoria_id and not crud.get_owned(db, "categorias", user_id, categoria_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if subcategoria_id and not crud.get_owned(db, "subcategorias", user_id, subcategoria_id):
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
    if conta_vinculada_id and not crud.get_owned(db, "contas", user_id, conta_vinculada_id):
        raise HTTPException(status_code=404, detail="Conta vinculada não encontrada")


def _chave_vinculo(categoria_id: str | None, subcategoria_id: str | None, conta_vinculada_id: str | None):
    """Mesma prioridade de orcamento_saldo.py (subcategoria > categoria >
    conta vinculada). None = item nome-livre, sem vínculo — nunca colide
    com outro (não há o que comparar)."""
    if subcategoria_id:
        return ("subcategoria_id", subcategoria_id)
    if categoria_id:
        return ("categoria_id", categoria_id)
    if conta_vinculada_id:
        return ("conta_vinculada_id", conta_vinculada_id)
    return None


def _check_vinculo_duplicado(
    db: Client,
    orcamento_id: str,
    bucket: str,
    categoria_id: str | None,
    subcategoria_id: str | None,
    conta_vinculada_id: str | None,
    item_id_excluir: str | None,
) -> None:
    """Achado 2026-10-10, corrigido 2026-10-11: a mesma categoria/
    subcategoria pode legitimamente estar em buckets diferentes (ex:
    "Espiritualidade" como custo fixo — dízimo — E sazonal — retiro
    ocasional; "Flamengo" fixo — mensalidade — E variável — compra
    avulsa). O que nunca faz sentido é 2 itens ATIVOS do MESMO bucket
    com o mesmo vínculo (quem seria o "equivalente" pra rolar
    saldo_anterior? Ordem de retorno da query, não tem significado de
    negócio). Bloqueado só dentro do mesmo bucket; o vazamento de
    realizado entre buckets diferentes foi corrigido na raiz, filtrando
    calcular_realizado_item(_em_lote) por estrutura_custo (ver
    docs/backlog.md). Item inativo não conta (não participa do cálculo
    ao vivo, ver carregar_dados_periodo)."""
    chave = _chave_vinculo(categoria_id, subcategoria_id, conta_vinculada_id)
    if chave is None:
        return
    campo, valor = chave
    itens_ativos = (
        db.table(ITENS_TABLE)
        .select("id,bucket,categoria_id,subcategoria_id,conta_vinculada_id")
        .eq("orcamento_id", orcamento_id)
        .eq("ativo", True)
        .execute()
        .data
    )
    for item in itens_ativos:
        if item_id_excluir and item["id"] == item_id_excluir:
            continue
        if item.get("bucket") == bucket and item.get(campo) == valor:
            raise HTTPException(
                status_code=409,
                detail="Já existe um item ativo para esse vínculo neste bucket.",
            )


def _insert_orcamento(db: Client, row: dict) -> dict:
    try:
        result = db.table(TABLE).insert(row).execute()
    except Exception as exc:  # noqa: BLE001 — traduzimos a violação de unicidade conhecida; o resto vai pro log
        if "duplicate key value violates unique constraint" in str(exc) or "23505" in str(exc):
            raise HTTPException(
                status_code=409,
                detail="Já existe um orçamento para este mês de vigência.",
            ) from exc
        print(f"[orcamentos] falha ao inserir: {exc!r} — row={row}")
        raise HTTPException(status_code=500, detail="Falha ao salvar o orçamento") from exc
    return result.data[0]


@router.get("", response_model=list[Orcamento])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = db.table(TABLE).select("*").eq("user_id", user_id).order("vigencia_mes", desc=True).execute()
    return result.data


@router.get("/{orcamento_id}", response_model=Orcamento)
def obter(orcamento_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return _get_orcamento_ou_404(db, user_id, orcamento_id)


@router.delete("/{orcamento_id}", status_code=204)
def apagar(orcamento_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Apaga o orçamento do mês e seus itens. Não mexe nos lançamentos reais
    (transações) nem em outro mês — `saldo_anterior` do mês seguinte, se
    existir, fica congelado com o valor já gravado até alguém gerar esse
    mês de novo. Item 56 do backlog: antes só era possível apagar como
    efeito colateral de `proximo-mes?substituir=true` (e só pro mês
    seguinte de um específico) — isto aqui é a ação direta, qualquer mês."""
    _get_orcamento_ou_404(db, user_id, orcamento_id)
    db.table(ITENS_TABLE).delete().eq("orcamento_id", orcamento_id).execute()
    db.table(TABLE).delete().eq("id", orcamento_id).eq("user_id", user_id).execute()


@router.post("", response_model=Orcamento, status_code=201)
def criar(payload: OrcamentoCreate, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    row = payload.model_dump(mode="json")
    # vigência é sempre o primeiro dia do mês, mesmo se vier outro dia
    row["vigencia_mes"] = date(payload.vigencia_mes.year, payload.vigencia_mes.month, 1).isoformat()
    row["user_id"] = user_id
    orcamento = _insert_orcamento(db, row)
    _popular_itens_de_transacoes_existentes(db, user_id, orcamento)
    return orcamento


@router.patch("/{orcamento_id}", response_model=Orcamento)
def atualizar(
    orcamento_id: str,
    payload: OrcamentoUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.update(db, TABLE, user_id, orcamento_id, payload.model_dump(exclude_unset=True))
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")


@router.get("/{orcamento_id}/itens", response_model=list[OrcamentoItem])
def listar_itens(orcamento_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    orcamento = _get_orcamento_ou_404(db, user_id, orcamento_id)
    result = db.table(ITENS_TABLE).select("*").eq("orcamento_id", orcamento_id).order("bucket").execute()
    contexto_saldo = _carregar_contexto_saldo(db, user_id, orcamento)
    return [_enriquecer_item(item, orcamento, contexto_saldo) for item in result.data]


@router.post("/{orcamento_id}/itens", response_model=OrcamentoItem, status_code=201)
def criar_item(
    orcamento_id: str,
    payload: OrcamentoItemCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    orcamento = _get_orcamento_ou_404(db, user_id, orcamento_id)
    _check_refs_item(db, user_id, payload.categoria_id, payload.subcategoria_id, payload.conta_vinculada_id)
    _check_vinculo_duplicado(
        db,
        orcamento_id,
        payload.bucket,
        payload.categoria_id,
        payload.subcategoria_id,
        payload.conta_vinculada_id,
        item_id_excluir=None,
    )
    contexto_saldo = _carregar_contexto_saldo(db, user_id, orcamento)
    row = payload.model_dump()
    row["orcamento_id"] = orcamento_id
    result = db.table(ITENS_TABLE).insert(row).execute()
    return _enriquecer_item(result.data[0], orcamento, contexto_saldo)


@router.patch("/{orcamento_id}/itens/{item_id}", response_model=OrcamentoItem)
def atualizar_item(
    orcamento_id: str,
    item_id: str,
    payload: OrcamentoItemUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    orcamento = _get_orcamento_ou_404(db, user_id, orcamento_id)
    item_atual = _get_item_ou_404(db, orcamento_id, item_id)
    dados = payload.model_dump(exclude_unset=True)
    _check_refs_item(
        db, user_id, dados.get("categoria_id"), dados.get("subcategoria_id"), dados.get("conta_vinculada_id")
    )
    if any(campo in dados for campo in ("bucket", "categoria_id", "subcategoria_id", "conta_vinculada_id")):
        _check_vinculo_duplicado(
            db,
            orcamento_id,
            dados.get("bucket", item_atual.get("bucket")),
            dados.get("categoria_id", item_atual.get("categoria_id")),
            dados.get("subcategoria_id", item_atual.get("subcategoria_id")),
            dados.get("conta_vinculada_id", item_atual.get("conta_vinculada_id")),
            item_id_excluir=item_id,
        )
    contexto_saldo = _carregar_contexto_saldo(db, user_id, orcamento)
    result = db.table(ITENS_TABLE).update(dados).eq("id", item_id).eq("orcamento_id", orcamento_id).execute()
    return _enriquecer_item(result.data[0], orcamento, contexto_saldo)


@router.patch("/{orcamento_id}/itens/{item_id}/ativo", response_model=OrcamentoItem)
def alternar_item_ativo(
    orcamento_id: str,
    item_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    orcamento = _get_orcamento_ou_404(db, user_id, orcamento_id)
    item_atual = _get_item_ou_404(db, orcamento_id, item_id)
    contexto_saldo = _carregar_contexto_saldo(db, user_id, orcamento)
    if ativo:
        # reativar pode reintroduzir vínculo duplicado (outro item ativo já
        # assumiu essa categoria/subcategoria/conta enquanto este estava
        # inativo)
        _check_vinculo_duplicado(
            db,
            orcamento_id,
            item_atual["bucket"],
            item_atual.get("categoria_id"),
            item_atual.get("subcategoria_id"),
            item_atual.get("conta_vinculada_id"),
            item_id_excluir=item_id,
        )
    result = (
        db.table(ITENS_TABLE).update({"ativo": ativo}).eq("id", item_id).eq("orcamento_id", orcamento_id).execute()
    )
    return _enriquecer_item(result.data[0], orcamento, contexto_saldo)


@router.post("/{orcamento_id}/proximo-mes", response_model=Orcamento, status_code=201)
def gerar_proximo_mes(
    orcamento_id: str,
    substituir: bool = Query(False),
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Modelo de envelope acumulativo combinado no redesign: cria o
    orçamento do mês seguinte com os mesmos itens (mesmo bucket/categoria/
    subcategoria/conta vinculada/`orcamento_mensal` — nunca o valor-base
    recorrente em si) do orçamento informado. `saldo_anterior` é gravado
    aqui, mas só é a fonte da verdade pra item "nome livre" (sem categoria/
    subcategoria/conta — não há como recalcular ao vivo sem transação pra
    rastrear). Pra item com vínculo, a leitura recalcula por cima
    (`_enriquecer_item`/`saldo_anterior_em_lote`), subindo até o mês
    anterior toda vez, em vez de confiar nesta coluna congelada no momento
    da geração — editar ou lançar algo no mês anterior depois de já ter
    gerado o seguinte atualiza a leitura sozinho, sem precisar gerar de
    novo.

    Se já existe um orçamento pro mês seguinte, recusa com 409 a menos que
    `substituir=true` seja passado — nesse caso apaga o orçamento (e seus
    itens) existente antes de gerar o novo no lugar dele."""
    atual = _get_orcamento_ou_404(db, user_id, orcamento_id)
    mes_atual = date.fromisoformat(atual["vigencia_mes"])
    mes_seguinte = somar_meses(mes_atual, 1)

    existente = (
        db.table(TABLE)
        .select("id")
        .eq("user_id", user_id)
        .eq("vigencia_mes", mes_seguinte.isoformat())
        .execute()
        .data
    )
    if existente and not substituir:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Já existe um orçamento para {mes_seguinte.isoformat()[:7]} — "
                "repita a chamada com substituir=true para sobrescrever."
            ),
        )
    if existente:
        existente_id = existente[0]["id"]
        db.table(ITENS_TABLE).delete().eq("orcamento_id", existente_id).execute()
        db.table(TABLE).delete().eq("id", existente_id).execute()

    novo_orcamento = _insert_orcamento(
        db,
        {
            "user_id": user_id,
            "vigencia_mes": mes_seguinte.isoformat(),
            "receita_base": atual["receita_base"],
            "percentual_geral": atual["percentual_geral"],
            "limite_custos_fixos": atual["limite_custos_fixos"],
            "limite_custos_variaveis": atual["limite_custos_variaveis"],
            "limite_sazonalidades": atual["limite_sazonalidades"],
            "limite_investimentos": atual["limite_investimentos"],
        },
    )

    itens_atuais = (
        db.table(ITENS_TABLE).select("*").eq("orcamento_id", orcamento_id).eq("ativo", True).execute().data
    )
    # em lote (1 busca de transações do mês, não 1 por item) — antes era
    # calcular_realizado_item por item, N+1 idas e voltas ao Supabase; com
    # uma conta real (dezenas de itens) isso deixava "Gerar orçamento"
    # visivelmente travado (achado 2026-09-29, mesma classe de bug já
    # corrigida em Estrutura de Custo/listagem de itens, Rodadas 27/29)
    _, _, transacoes_por_mes = carregar_dados_periodo(db, user_id, mes_atual, mes_atual)
    transacoes_do_mes = transacoes_por_mes.get(mes_atual.isoformat(), [])
    # 1 insert em lote com todos os itens copiados, não 1 insert por item —
    # mesma classe de N+1 do `_popular_itens_de_transacoes_existentes`
    # abaixo, achado junto (2026-09-30)
    novos_itens = []
    for item in itens_atuais:
        # o valor gravado aqui só importa de verdade pra item "nome livre"
        # (sem categoria/subcategoria/conta) — esse tipo nunca tem como
        # recalcular ao vivo (não há transação pra rastrear), então precisa
        # nascer certo. Pra item com vínculo, a leitura sempre recalcula por
        # cima (_enriquecer_item/saldo_anterior_em_lote) e ignora isto —
        # gravar aqui não atrapalha, só deixa de ser a fonte da verdade.
        realizado = calcular_realizado_item_em_lote(item, transacoes_do_mes)
        disponivel_neste_mes = round(item["orcamento_mensal"] + item.get("saldo_anterior", 0), 2)
        novos_itens.append(
            {
                "orcamento_id": novo_orcamento["id"],
                "bucket": item["bucket"],
                "categoria_id": item.get("categoria_id"),
                "subcategoria_id": item.get("subcategoria_id"),
                "nome": item.get("nome"),
                "conta_vinculada_id": item.get("conta_vinculada_id"),
                "orcamento_mensal": item["orcamento_mensal"],
                "saldo_anterior": round(disponivel_neste_mes - realizado, 2),
            }
        )
    if novos_itens:
        db.table(ITENS_TABLE).insert(novos_itens).execute()

    _popular_itens_de_transacoes_existentes(db, user_id, novo_orcamento)
    return novo_orcamento
