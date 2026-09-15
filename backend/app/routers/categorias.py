from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.categorias import Categoria, CategoriaCreate, CategoriaUpdate, TipoCategoria
from ..services import crud

router = APIRouter(prefix="/categorias", tags=["categorias"])
TABLE = "categorias"

_JANELA_USO_DIAS = 180  # ~6 meses — janela considerada pra "mais usadas"


@router.get("", response_model=list[Categoria])
def listar(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    tipo: TipoCategoria | None = None,
):
    categorias = crud.list_all(db, TABLE, user_id)
    if tipo:
        categorias = [c for c in categorias if c["tipo"] == tipo]
    return categorias


@router.get("/mais-usadas", response_model=list[Categoria])
def mais_usadas(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    tipo: TipoCategoria | None = None,
    limite: int = 5,
):
    """Ranking por frequência de uso nos últimos ~6 meses — pra sugerir
    atalhos no formulário de lançamento em vez de forçar navegar o select
    inteiro toda vez. Precisa vir antes de /{categoria_id} na declaração de
    rotas, senão "mais-usadas" seria capturado como um categoria_id."""
    desde = (date.today() - timedelta(days=_JANELA_USO_DIAS)).isoformat()
    transacoes = (
        db.table("transacoes")
        .select("categoria_id")
        .eq("user_id", user_id)
        .gte("data_compra", desde)
        .execute()
        .data
    )
    contagem: dict[str, int] = {}
    for t in transacoes:
        if t["categoria_id"]:
            contagem[t["categoria_id"]] = contagem.get(t["categoria_id"], 0) + 1

    categorias = [c for c in crud.list_all(db, TABLE, user_id) if c["ativo"]]
    if tipo:
        categorias = [c for c in categorias if c["tipo"] == tipo]
    categorias.sort(key=lambda c: (-contagem.get(c["id"], 0), c["nome"]))
    return categorias[:limite]


@router.get("/{categoria_id}", response_model=Categoria)
def obter(categoria_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, categoria_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")


@router.post("", response_model=Categoria, status_code=201)
def criar(payload: CategoriaCreate, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.create(db, TABLE, user_id, payload.model_dump())


@router.patch("/{categoria_id}", response_model=Categoria)
def atualizar(
    categoria_id: str,
    payload: CategoriaUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.update(db, TABLE, user_id, categoria_id, payload.model_dump(exclude_unset=True))
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")


@router.patch("/{categoria_id}/ativo", response_model=Categoria)
def alternar_ativo(
    categoria_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.set_ativo(db, TABLE, user_id, categoria_id, ativo)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
