from typing import Literal

from pydantic import BaseModel

EstruturaCusto = Literal["fixo", "variavel", "sazonal", "investimentos"]


class SubcategoriaCreate(BaseModel):
    categoria_id: str
    nome: str
    # sugestão pré-preenchida no formulário de lançamento; None força escolha
    # explícita (subcategorias sabidamente mistas, ex: Lazer > Viagens)
    estrutura_custo_padrao: EstruturaCusto | None = None


class SubcategoriaUpdate(BaseModel):
    nome: str | None = None
    estrutura_custo_padrao: EstruturaCusto | None = None


class Subcategoria(SubcategoriaCreate):
    id: str
    ativo: bool
