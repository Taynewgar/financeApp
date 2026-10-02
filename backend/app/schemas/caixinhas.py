from pydantic import BaseModel


class CaixinhaCreate(BaseModel):
    nome: str
    conta_id: str | None = None


class CaixinhaUpdate(BaseModel):
    nome: str | None = None
    conta_id: str | None = None


class Caixinha(CaixinhaCreate):
    id: str
    ativo: bool
