from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.caixinhas import Caixinha, CaixinhaCreate, CaixinhaUpdate
from ..services import crud

router = APIRouter(prefix="/caixinhas", tags=["caixinhas"])
TABLE = "caixinhas"

_JANELA_USO_DIAS = 180  # ~6 meses — mesmo padrão de categorias/subcategorias mais-usadas


def _check_conta(db: Client, user_id: str, conta_id: str | None) -> None:
    if conta_id and not crud.get_owned(db, "contas", user_id, conta_id):
        raise HTTPException(status_code=404, detail="Conta vinculada não encontrada")


@router.get("", response_model=list[Caixinha])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


@router.get("/mais-usadas", response_model=list[Caixinha])
def mais_usadas(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limite: int = 5,
):
    """Ranking por frequência de uso (aporte OU retirada) nos últimos ~6
    meses — mesmo padrão de /categorias/mais-usadas e /subcategorias/mais-
    usadas. Usado pelo picker do Comparador de Séries (item 51/91: corte
    "mais usadas" nas abas com muitos itens). Precisa vir antes de
    /{caixinha_id} na declaração de rotas, senão "mais-usadas" seria
    capturado como um caixinha_id."""
    desde = (date.today() - timedelta(days=_JANELA_USO_DIAS)).isoformat()
    transacoes = crud.buscar_todas_paginado(
        lambda: db.table("transacoes").select("caixinha_id").eq("user_id", user_id).gte("data_compra", desde)
    )
    contagem: dict[str, int] = {}
    for t in transacoes:
        if t["caixinha_id"]:
            contagem[t["caixinha_id"]] = contagem.get(t["caixinha_id"], 0) + 1

    caixinhas = [c for c in crud.list_all(db, TABLE, user_id) if c["ativo"]]
    caixinhas.sort(key=lambda c: (-contagem.get(c["id"], 0), c["nome"]))
    return caixinhas[:limite]


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
