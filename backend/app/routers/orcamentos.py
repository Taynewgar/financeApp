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

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])
TABLE = "orcamentos"
ITENS_TABLE = "orcamento_itens"


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
    return result.data


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
    return result.data[0]


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
    return result.data[0]


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
    return result.data[0]
