from datetime import date

from pydantic import BaseModel


class ItemEstruturaCusto(BaseModel):
    # exatamente um destes é preenchido (ou nenhum, se a transação não tem
    # categoria/subcategoria nem é de uma conta de investimento vinculada)
    categoria_id: str | None = None
    subcategoria_id: str | None = None
    conta_id: str | None = None
    orcado: float
    realizado: float


class BucketEstruturaCusto(BaseModel):
    bucket: str
    orcado: float
    realizado: float
    itens: list[ItemEstruturaCusto]


class VereditoTeto(BaseModel):
    """custos_fixos + custos_variaveis + sazonalidades tratados como um teto
    único (percentual dos 3 buckets + saldo_anterior acumulado dos itens
    deles) — estourar um bucket individualmente não compromete o mês se
    outro bucket do pool tiver folga suficiente para compensar."""

    teto: float
    realizado: float
    dentro_do_teto: bool


class VereditoPiso(BaseModel):
    """investimentos é o inverso: não é teto, é piso — a meta é bater pelo
    menos esse valor (teto% + saldo_anterior acumulado), sobrar é bom."""

    teto: float
    realizado: float
    meta_batida: bool


class EstruturaCustoMes(BaseModel):
    vigencia_mes: date
    # None quando não existe orçamento criado para este mês — a leitura de
    # realizado funciona de qualquer forma, só "orcado" fica zerado
    orcamento_id: str | None = None
    buckets: list[BucketEstruturaCusto]
    # None junto com orcamento_id — sem orçamento não há teto pra comparar
    pool_despesas: VereditoTeto | None = None
    piso_investimentos: VereditoPiso | None = None
