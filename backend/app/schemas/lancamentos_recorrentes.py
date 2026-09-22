from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .transacoes import MeioPagamento

# só despesa fixa recorrente (aluguel, assinatura) — sem 'investimentos'
# (aporte não é despesa recorrente, ver estrutura_custo.py)
EstruturaCustoRecorrente = Literal["fixo", "variavel", "sazonal"]


class LancamentoRecorrenteCreate(BaseModel):
    descricao: str
    valor: float = Field(gt=0)
    dia_mes: int = Field(ge=1, le=31)
    conta_id: str
    categoria_id: str
    subcategoria_id: str | None = None
    estrutura_custo: EstruturaCustoRecorrente
    meio_pagamento: MeioPagamento
    data_inicio: date
    data_fim: date | None = None


class LancamentoRecorrenteUpdate(BaseModel):
    descricao: str | None = None
    valor: float | None = Field(default=None, gt=0)
    dia_mes: int | None = Field(default=None, ge=1, le=31)
    conta_id: str | None = None
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    estrutura_custo: EstruturaCustoRecorrente | None = None
    meio_pagamento: MeioPagamento | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class LancamentoRecorrente(LancamentoRecorrenteCreate):
    id: str
    ativo: bool


class VigenciaMesPayload(BaseModel):
    """Corpo compartilhado por /confirmar e /pular — os dois só precisam
    saber qual mês (primeiro dia do mês de vigência)."""

    vigencia_mes: date


class MesPulado(BaseModel):
    id: str
    lancamento_recorrente_id: str
    vigencia_mes: date
