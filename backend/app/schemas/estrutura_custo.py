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


class EstruturaCustoMes(BaseModel):
    vigencia_mes: date
    # None quando não existe orçamento criado para este mês — a leitura de
    # realizado funciona de qualquer forma, só "orcado" fica zerado
    orcamento_id: str | None = None
    buckets: list[BucketEstruturaCusto]
