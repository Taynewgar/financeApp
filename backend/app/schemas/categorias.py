from typing import Literal

from pydantic import BaseModel

# receita e investimento têm 1 categoria "pai" fixa por usuário (a escolha
# do lançamento fica só na subcategoria); despesa é onde mora a variedade
# real de categorias/subcategorias — ver regra em transacoes.py
TipoCategoria = Literal["receita", "despesa", "investimento"]


class CategoriaCreate(BaseModel):
    nome: str
    tipo: TipoCategoria = "despesa"


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    tipo: TipoCategoria | None = None


class Categoria(CategoriaCreate):
    id: str
    ativo: bool
