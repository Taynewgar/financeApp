from datetime import date

from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])
TABLE = "orcamentos"
ITENS_TABLE = "orcamento_itens"

# sinal de cada tipo de movimento para o cálculo de realizado — despesa conta
# a favor do gasto, estorno/ressarcimento reduz (é dinheiro devolvido);
# aplicacao/retirada só entram para itens de investimento (via conta_vinculada_id)
_SINAL_REALIZADO = {
    "despesa": 1,
    "estorno": -1,
    "ressarcimento": -1,
    "aplicacao": 1,
    "retirada": -1,
}


def _com_disponivel(item: dict) -> dict:
    return {**item, "disponivel": round(item["orcamento_mensal"] + item.get("saldo_anterior", 0), 2)}


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


@router.post("", response_model=Orcamento, status_code=201)
def criar(payload: OrcamentoCreate, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    row = payload.model_dump(mode="json")
    # vigência é sempre o primeiro dia do mês, mesmo se vier outro dia
    row["vigencia_mes"] = date(payload.vigencia_mes.year, payload.vigencia_mes.month, 1).isoformat()
    row["user_id"] = user_id
    return _insert_orcamento(db, row)


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
    _get_orcamento_ou_404(db, user_id, orcamento_id)
    result = db.table(ITENS_TABLE).select("*").eq("orcamento_id", orcamento_id).order("bucket").execute()
    return [_com_disponivel(item) for item in result.data]


@router.post("/{orcamento_id}/itens", response_model=OrcamentoItem, status_code=201)
def criar_item(
    orcamento_id: str,
    payload: OrcamentoItemCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _get_orcamento_ou_404(db, user_id, orcamento_id)
    _check_refs_item(db, user_id, payload.categoria_id, payload.subcategoria_id, payload.conta_vinculada_id)
    row = payload.model_dump()
    row["orcamento_id"] = orcamento_id
    result = db.table(ITENS_TABLE).insert(row).execute()
    return _com_disponivel(result.data[0])


@router.patch("/{orcamento_id}/itens/{item_id}", response_model=OrcamentoItem)
def atualizar_item(
    orcamento_id: str,
    item_id: str,
    payload: OrcamentoItemUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _get_orcamento_ou_404(db, user_id, orcamento_id)
    _get_item_ou_404(db, orcamento_id, item_id)
    dados = payload.model_dump(exclude_unset=True)
    _check_refs_item(
        db, user_id, dados.get("categoria_id"), dados.get("subcategoria_id"), dados.get("conta_vinculada_id")
    )
    result = db.table(ITENS_TABLE).update(dados).eq("id", item_id).eq("orcamento_id", orcamento_id).execute()
    return _com_disponivel(result.data[0])


@router.patch("/{orcamento_id}/itens/{item_id}/ativo", response_model=OrcamentoItem)
def alternar_item_ativo(
    orcamento_id: str,
    item_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _get_orcamento_ou_404(db, user_id, orcamento_id)
    _get_item_ou_404(db, orcamento_id, item_id)
    result = (
        db.table(ITENS_TABLE).update({"ativo": ativo}).eq("id", item_id).eq("orcamento_id", orcamento_id).execute()
    )
    return _com_disponivel(result.data[0])


def _calcular_realizado(db: Client, user_id: str, item: dict, mes_inicio: date, mes_fim: date) -> float:
    """Soma as transações do período que contam para este item — por
    categoria/subcategoria para os buckets de custo, ou pela conta vinculada
    para itens de investimento. Sem nenhum dos três vínculos, não há como
    calcular realizado (o item é só uma linha de planejamento livre)."""
    query = (
        db.table("transacoes")
        .select("valor,tipo_movimento")
        .eq("user_id", user_id)
        .gte("data_compra", mes_inicio.isoformat())
        .lt("data_compra", mes_fim.isoformat())
    )
    if item.get("categoria_id"):
        query = query.eq("categoria_id", item["categoria_id"])
    elif item.get("subcategoria_id"):
        query = query.eq("subcategoria_id", item["subcategoria_id"])
    elif item.get("conta_vinculada_id"):
        query = query.eq("conta_id", item["conta_vinculada_id"])
    else:
        return 0.0

    total = sum(
        _SINAL_REALIZADO.get(t["tipo_movimento"], 0) * t["valor"] for t in query.execute().data
    )
    return round(total, 2)


@router.post("/{orcamento_id}/proximo-mes", response_model=Orcamento, status_code=201)
def gerar_proximo_mes(
    orcamento_id: str,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Modelo de envelope acumulativo combinado no redesign: fecha o mês do
    orçamento informado calculando o realizado de cada item contra as
    transações do período, e cria o orçamento do mês seguinte com a sobra
    (ou o estouro, se o item passou do previsto) já somada em
    `saldo_anterior` de cada item — nunca alterando `orcamento_mensal`, que
    continua sendo o valor-base recorrente."""
    atual = _get_orcamento_ou_404(db, user_id, orcamento_id)
    mes_atual = date.fromisoformat(atual["vigencia_mes"])
    mes_seguinte = somar_meses(mes_atual, 1)

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
    for item in itens_atuais:
        realizado = _calcular_realizado(db, user_id, item, mes_atual, mes_seguinte)
        disponivel_neste_mes = round(item["orcamento_mensal"] + item.get("saldo_anterior", 0), 2)
        db.table(ITENS_TABLE).insert(
            {
                "orcamento_id": novo_orcamento["id"],
                "bucket": item["bucket"],
                "categoria_id": item.get("categoria_id"),
                "subcategoria_id": item.get("subcategoria_id"),
                "nome": item.get("nome"),
                "conta_vinculada_id": item.get("conta_vinculada_id"),
                "orcamento_mensal": item["orcamento_mensal"],
                "percentual": item.get("percentual", 0),
                "saldo_anterior": round(disponivel_neste_mes - realizado, 2),
            }
        ).execute()

    return novo_orcamento
