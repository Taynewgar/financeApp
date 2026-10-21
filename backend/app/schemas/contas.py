from typing import Literal

from pydantic import BaseModel, Field

TipoConta = Literal["corrente", "cartao_credito", "carteira", "caixinha", "investimento"]


class ContaCreate(BaseModel):
    nome: str
    tipo_conta: TipoConta
    banco: str | None = None
    saldo_inicial: float = 0
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)


class ContaUpdate(BaseModel):
    nome: str | None = None
    banco: str | None = None
    saldo_inicial: float | None = None
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)


class Conta(ContaCreate):
    id: str
    ativo: bool
