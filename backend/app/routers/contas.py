from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.contas import Conta, ContaCreate, ContaUpdate
from ..services import crud

router = APIRouter(prefix="/contas", tags=["contas"])
TABLE = "contas"


@router.get("", response_model=list[Conta])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


@router.get("/{conta_id}", response_model=Conta)
def obter(conta_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, conta_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Conta não encontrada")


@router.post("", response_model=Conta, status_code=201)
def criar(payload: ContaCreate, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.create(db, TABLE, user_id, payload.model_dump())


@router.patch("/{conta_id}", response_model=Conta)
def atualizar(
    conta_id: str,
    payload: ContaUpdate,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.update(db, TABLE, user_id, conta_id, payload.model_dump(exclude_unset=True))
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Conta não encontrada")


@router.patch("/{conta_id}/ativo", response_model=Conta)
def alternar_ativo(
    conta_id: str,
    ativo: bool,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return crud.set_ativo(db, TABLE, user_id, conta_id, ativo)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
