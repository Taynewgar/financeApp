from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .transacoes import EstruturaCusto, MeioPagamento

# recorrente cobre os 4 tipos que de fato repetem todo mês (salário,
# aluguel, aporte mensal) — estorno/ressarcimento não fazem sentido como
# molde recorrente, só existem vinculados a uma despesa específica já
# lançada (ver TipoMovimento em schemas/transacoes.py)
TipoMovimentoRecorrente = Literal["receita", "despesa", "aplicacao", "retirada"]


class LancamentoRecorrenteCreate(BaseModel):
    descricao: str
    valor: float = Field(gt=0)
    dia_mes: int = Field(ge=1, le=31)
    tipo_movimento: TipoMovimentoRecorrente
    conta_id: str
    categoria_id: str
    subcategoria_id: str | None = None
    # obrigatório só pra despesa (fixo/variavel/sazonal); aplicação/retirada
    # é sempre 'investimentos' (forçado pelo servidor, ver routers/
    # lancamentos_recorrentes.py); receita não usa — ver README.md, seção
    # "Lançamentos Recorrentes"
    estrutura_custo: EstruturaCusto | None = None
    # obrigatório só pra despesa; receita/aplicação/retirada não usam
    meio_pagamento: MeioPagamento | None = None
    data_inicio: date
    data_fim: date | None = None


class LancamentoRecorrenteUpdate(BaseModel):
    descricao: str | None = None
    valor: float | None = Field(default=None, gt=0)
    dia_mes: int | None = Field(default=None, ge=1, le=31)
    tipo_movimento: TipoMovimentoRecorrente | None = None
    conta_id: str | None = None
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    estrutura_custo: EstruturaCusto | None = None
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
