from datetime import date
from typing import Literal

from pydantic import BaseModel


class _CamposFinanceiros(BaseModel):
    """Os mesmos campos que calcular_resumo() devolve, compartilhados entre
    o resumo de um mês (ResumoMensal) e o de um período livre (ResumoPeriodo)
    — só muda o que identifica QUAL recorte de tempo é esse."""

    receitas: float
    despesas_brutas: float
    despesas_liquidas: float
    ajustes_vinculados: float
    ajustes_nao_vinculados: float
    aplicacoes: float
    retiradas: float
    # reserva: aplicação/retirada COM caixinha vinculada (guardar dinheiro)
    reservas: float
    # investimento: aplicação/retirada SEM caixinha (mesma distinção de
    # estrutura_custo.py) — conceito diferente de reserva
    investimentos: float
    # fluxo de caixa: o que de fato entrou/saiu, sem nenhum ajuste
    resultado_fluxo_caixa: float
    # saúde financeira: receita + ajustes soltos (não vinculados a uma
    # despesa específica) menos despesas já líquidas dos ajustes vinculados
    resultado_saude: float
    # resultado_saude / (receitas + ajustes_nao_vinculados) — None se essa
    # base for zero (não dá pra calcular taxa sobre receita ajustada nula)
    taxa_poupanca: float | None = None


class ResumoMensal(_CamposFinanceiros):
    vigencia_mes: date


class ResumoPeriodo(_CamposFinanceiros):
    """Mesmo cálculo de ResumoMensal, mas somado sobre um período livre
    (modo Intervalo/Todos os meses do seletor do Dashboard) em vez de um
    único mês — por isso não é aditivo mês a mês (taxa_poupanca em
    particular precisa ser recalculada sobre o total do período, não a
    média dos meses)."""

    inicio: date
    fim: date


class PontoEvolucaoMensal(ResumoMensal):
    resultado_saude_acumulado: float
    taxa_poupanca_acumulada: float | None = None


class EvolucaoMensal(BaseModel):
    inicio: date
    fim: date
    meses: list[PontoEvolucaoMensal]


class SaldoCaixinha(BaseModel):
    id: str
    nome: str
    saldo: float


class CompromissoFuturo(BaseModel):
    tipo: Literal["parcela", "recorrente"]
    descricao: str | None
    valor: float
    data_compra: date
    # compra parcelada é sempre despesa; recorrente carrega o tipo do
    # próprio molde (pode ser receita/aplicação/retirada também, ver
    # README.md "Lançamentos Recorrentes") — usado pro rótulo/cor no
    # Dashboard (Compromissos Futuros)
    tipo_movimento: Literal["receita", "despesa", "aplicacao", "retirada"]
    parcela_atual: int | None = None
    parcela_total: int | None = None
    # só presente quando tipo == "recorrente" — usado pelo botão "Confirmar"
    # (POST /lancamentos-recorrentes/{id}/confirmar)
    lancamento_recorrente_id: str | None = None


class PrimeiroMes(BaseModel):
    vigencia_mes: date | None


class DespesaPorCategoria(BaseModel):
    categoria_id: str
    categoria_nome: str
    valor: float
    percentual: float


class DespesaPorSubcategoria(BaseModel):
    # None = despesa sem subcategoria (agrupada em "Sem subcategoria")
    subcategoria_id: str | None
    subcategoria_nome: str
    valor: float
    percentual: float
