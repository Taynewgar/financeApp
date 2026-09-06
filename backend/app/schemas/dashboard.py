from datetime import date

from pydantic import BaseModel


class ResumoMensal(BaseModel):
    vigencia_mes: date
    receitas: float
    despesas_brutas: float
    despesas_liquidas: float
    ajustes_vinculados: float
    ajustes_nao_vinculados: float
    aplicacoes: float
    retiradas: float
    reservas: float
    # fluxo de caixa: o que de fato entrou/saiu, sem nenhum ajuste
    resultado_fluxo_caixa: float
    # saúde financeira: receita + ajustes soltos (não vinculados a uma
    # despesa específica) menos despesas já líquidas dos ajustes vinculados
    resultado_saude: float
    # resultado_saude / (receitas + ajustes_nao_vinculados) — None se essa
    # base for zero (não dá pra calcular taxa sobre receita ajustada nula)
    taxa_poupanca: float | None = None


class PontoEvolucaoMensal(ResumoMensal):
    resultado_saude_acumulado: float
    taxa_poupanca_acumulada: float | None = None


class EvolucaoMensal(BaseModel):
    inicio: date
    fim: date
    meses: list[PontoEvolucaoMensal]
