from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nome: str


class CategoriaUpdate(BaseModel):
    nome: str | None = None


class Categoria(CategoriaCreate):
    id: str
    ativo: bool
