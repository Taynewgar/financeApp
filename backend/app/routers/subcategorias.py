from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..auth import get_current_user_id, get_db
from ..schemas.subcategorias import Subcategoria, SubcategoriaCreate, SubcategoriaUpdate
from ..services import crud

router = APIRouter(prefix="/subcategorias", tags=["subcategorias"])
TABLE = "subcategorias"

_JANELA_USO_DIAS = 180  # ~6 meses — janela considerada pra "mais usadas"


@router.get("", response_model=list[Subcategoria])
def listar(db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return crud.list_all(db, TABLE, user_id)


@router.get("/mais-usadas", response_model=list[Subcategoria])
def mais_usadas(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    categoria_id: str | None = None,
    limite: int = 5,
):
    """Ranking por frequência de uso nos últimos ~6 meses, igual à mesma
    rota em categorias.py — mesmo motivo de precisar vir antes de
    /{subcategoria_id} na declaração de rotas."""
    desde = (date.today() - timedelta(days=_JANELA_USO_DIAS)).isoformat()
    transacoes = crud.buscar_todas_paginado(
        lambda: db.table("transacoes").select("subcategoria_id").eq("user_id", user_id).gte("data_compra", desde)
    )
    contagem: dict[str, int] = {}
    for t in transacoes:
        if t["subcategoria_id"]:
            contagem[t["subcategoria_id"]] = contagem.get(t["subcategoria_id"], 0) + 1

    subcategorias = [s for s in crud.list_all(db, TABLE, user_id) if s["ativo"]]
    if categoria_id:
        subcategorias = [s for s in subcategorias if s["categoria_id"] == categoria_id]
    subcategorias.sort(key=lambda s: (-contagem.get(s["id"], 0), s["nome"]))
    return subcategorias[:limite]


@router.get("/{subcategoria_id}", response_model=Subcategoria)
def obter(subcategoria_id: str, db: Client = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    try:
        return crud.get_one(db, TABLE, user_id, subcategoria_id)
    except crud.NotFound:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada")


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
    dados = payload.model_dump(exclude_unset=True)
    if "categoria_id" in dados:
        # mover subcategoria pra outra categoria pai (item 48 do backlog)
        # — só entre categorias tipo despesa: é onde mora a variedade de
        # subcategorias de verdade, receita/investimento têm 1 categoria
        # pai fixa cada, sem uso real pra subcategoria mudar pra lá
        nova_categoria = (
            db.table("categorias").select("id,tipo").eq("id", dados["categoria_id"]).eq("user_id", user_id).execute()
        ).data
        if not nova_categoria:
            raise HTTPException(status_code=404, detail="Categoria pai não encontrada")
        if nova_categoria[0]["tipo"] != "despesa":
            raise HTTPException(status_code=422, detail="Só é possível mover a subcategoria para outra categoria de despesa")
    try:
        return crud.update(db, TABLE, user_id, subcategoria_id, dados)
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
