from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.subcategorias import Subcategoria, SubcategoriaCreate, SubcategoriaUpdate
from ..services import crud

router = APIRouter(prefix="/subcategorias", tags=["subcategorias"])
TABLE = "subcategorias"


@router.get("", response_model=list[Subcategoria])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


@router.post("", response_model=Subcategoria, status_code=201)
def criar(
    payload: SubcategoriaCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if not crud.get_owned(db, "categorias", user_id, payload.categoria_id):
        raise HTTPException(status_code=404, detail="Categoria pai não encontrada")
    return crud.create(db, TABLE, user_id, payload.model_dump())


@router.patch("/{subcategoria_id}", response_model=Subcategoria)
def atualizar(
    subcategoria_id: str,
    payload: SubcategoriaUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.update(db, TABLE, user_id, subcategoria_id, payload.model_dump(exclude_unset=True))
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")


@router.patch("/{subcategoria_id}/ativo", response_model=Subcategoria)
def alternar_ativo(
    subcategoria_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.set_ativo(db, TABLE, user_id, subcategoria_id, ativo)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")
