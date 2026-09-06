from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoMovimento = Literal["receita", "despesa", "aplicacao", "retirada", "estorno", "ressarcimento"]
EstruturaCusto = Literal["fixo", "variavel", "sazonal"]
# etiqueta descritiva de como a transação saiu da conta — sem saldo próprio
# nem transferência entre contas, só metadado pra filtro/análise (ex:
# distinguir Pix de boleto dentro da mesma conta corrente)
MeioPagamento = Literal["pix", "cartao_debito", "boleto", "debito_automatico", "dinheiro", "transferencia", "outro"]


class TransacaoCreate(BaseModel):
    data_compra: date
    valor: float = Field(ge=0)
    descricao: str | None = None
    tipo_movimento: TipoMovimento
    conta_id: str
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    # editável mesmo quando a subcategoria sugere um valor (categorias
    # mistas como Lazer podem ter gastos em mais de uma estrutura)
    estrutura_custo: EstruturaCusto | None = None
    caixinha_id: str | None = None
    meio_pagamento: MeioPagamento | None = None
    # vincula um estorno/ressarcimento à despesa original
    ajuste_de_transacao_id: str | None = None


class CompraParceladaCreate(BaseModel):
    descricao: str
    valor_total: float = Field(gt=0)
    parcela_total: int = Field(ge=1, le=48)
    data_primeira_parcela: date
    conta_id: str
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    estrutura_custo: EstruturaCusto | None = None
    meio_pagamento: MeioPagamento | None = None


class MoverFaturaPayload(BaseModel):
    fatura_referencia: date


class ResumoLancamentos(BaseModel):
    total_lancamentos: int
    receitas: float
    despesas_brutas: float
    despesas_liquidas: float
    ajustes_vinculados: float
    ajustes_nao_vinculados: float
    aplicacoes: float
    retiradas: float
    reservas: float
    resultado_fluxo_caixa: float
    resultado_saude: float
    taxa_poupanca: float | None = None


class Transacao(BaseModel):
    id: str
    data_compra: date
    valor: float
    descricao: str | None = None
    tipo_movimento: TipoMovimento
    pagamento: Literal["avista", "parcelado"]
    parcela_atual: int | None = None
    parcela_total: int | None = None
    compra_parcelada_id: str | None = None
    conta_id: str
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    estrutura_custo: EstruturaCusto | None = None
    caixinha_id: str | None = None
    meio_pagamento: MeioPagamento | None = None
    fatura_referencia: date | None = None
    fatura_override: bool
    ajuste_de_transacao_id: str | None = None
