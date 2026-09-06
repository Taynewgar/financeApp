from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.caixinhas import Caixinha, CaixinhaCreate, CaixinhaUpdate
from ..services import crud

router = APIRouter(prefix="/caixinhas", tags=["caixinhas"])
TABLE = "caixinhas"


def _check_conta(db: Client, user_id: str, conta_id: str | None) -> None:
    if conta_id and not crud.get_owned(db, "contas", user_id, conta_id):
        raise HTTPException(status_code=404, detail="Conta vinculada não encontrada")


@router.get("", response_model=list[Caixinha])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


@router.get("/{caixinha_id}", response_model=Caixinha)
def obter(caixinha_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, caixinha_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")


@router.post("", response_model=Caixinha, status_code=201)
def criar(
    payload: CaixinhaCreate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _check_conta(db, user_id, payload.conta_id)
    return crud.create(db, TABLE, user_id, payload.model_dump())


@router.patch("/{caixinha_id}", response_model=Caixinha)
def atualizar(
    caixinha_id: str,
    payload: CaixinhaUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    _check_conta(db, user_id, payload.conta_id)
    try:
        return crud.update(db, TABLE, user_id, caixinha_id, payload.model_dump(exclude_unset=True))
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")


@router.patch("/{caixinha_id}/ativo", response_model=Caixinha)
def alternar_ativo(
    caixinha_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.set_ativo(db, TABLE, user_id, caixinha_id, ativo)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Caixinha não encontrada")
