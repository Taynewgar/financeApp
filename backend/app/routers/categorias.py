from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.categorias import Categoria, CategoriaCreate, CategoriaUpdate
from ..services import crud

router = APIRouter(prefix="/categorias", tags=["categorias"])
TABLE = "categorias"


@router.get("", response_model=list[Categoria])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


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
