from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Bucket = Literal["custos_fixos", "custos_variaveis", "sazonalidades", "investimentos"]


class OrcamentoCreate(BaseModel):
    vigencia_mes: date
    receita_base: float = Field(ge=0, default=0)
    percentual_geral: float = Field(ge=0, le=100, default=0)
    limite_custos_fixos: float = Field(ge=0, le=100, default=40)
    limite_custos_variaveis: float = Field(ge=0, le=100, default=25)
    limite_sazonalidades: float = Field(ge=0, le=100, default=10)
    limite_investimentos: float = Field(ge=0, le=100, default=25)


class OrcamentoUpdate(BaseModel):
    receita_base: float | None = Field(default=None, ge=0)
    percentual_geral: float | None = Field(default=None, ge=0, le=100)
    limite_custos_fixos: float | None = Field(default=None, ge=0, le=100)
    limite_custos_variaveis: float | None = Field(default=None, ge=0, le=100)
    limite_sazonalidades: float | None = Field(default=None, ge=0, le=100)
    limite_investimentos: float | None = Field(default=None, ge=0, le=100)


class Orcamento(OrcamentoCreate):
    id: str


class OrcamentoItemCreate(BaseModel):
    bucket: Bucket
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    # usado por itens sem categoria (ex: "Liberdade Financeira" em investimentos)
    nome: str | None = None
    # liga um item de investimento/reserva à conta real que guarda o saldo
    conta_vinculada_id: str | None = None
    orcamento_mensal: float = Field(ge=0, default=0)
    percentual: float = Field(ge=0, le=100, default=0)


class OrcamentoItemUpdate(BaseModel):
    bucket: Bucket | None = None
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    nome: str | None = None
    conta_vinculada_id: str | None = None
    orcamento_mensal: float | None = Field(default=None, ge=0)
    percentual: float | None = Field(default=None, ge=0, le=100)


class OrcamentoItem(OrcamentoItemCreate):
    id: str
    orcamento_id: str
    ativo: bool
