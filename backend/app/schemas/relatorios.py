from datetime import date
from typing import Literal

from pydantic import BaseModel

from .dashboard import DespesaPorCategoria, DespesaPorSubcategoria, PontoEvolucaoMensal, ResumoMensal, ResumoPeriodo, SaldoCaixinha
from .estrutura_custo import EstruturaCustoMes
from .transacoes import Transacao


class PeriodoRelatorio(BaseModel):
    tipo: Literal["mes", "ano"]
    inicio: date
    fim: date


class LancamentoExportado(Transacao):
    """Mesmos campos de Transacao, com os ids de categoria/subcategoria/
    conta/caixinha também resolvidos pro nome — pensado pra ser lido fora
    do app (colado numa conversa, aberto em outra ferramenta de análise),
    sem precisar cruzar com outra tabela pra saber o que cada id significa."""

    categoria_nome: str | None = None
    subcategoria_nome: str | None = None
    conta_nome: str | None = None
    caixinha_nome: str | None = None
    caixinha_origem_nome: str | None = None


class RelatorioMensal(BaseModel):
    periodo: PeriodoRelatorio
    resumo: ResumoMensal
    lancamentos: list[LancamentoExportado]
    despesas_por_categoria: list[DespesaPorCategoria]
    despesas_por_subcategoria: list[DespesaPorSubcategoria]
    estrutura_custo: EstruturaCustoMes
    caixinhas_patrimonio: list[SaldoCaixinha]
    retiradas_pendentes: list[Transacao]


class RelatorioAnual(BaseModel):
    periodo: PeriodoRelatorio
    resumo: ResumoPeriodo
    evolucao_mensal: list[PontoEvolucaoMensal]
    lancamentos: list[LancamentoExportado]
    despesas_por_categoria: list[DespesaPorCategoria]
    despesas_por_subcategoria: list[DespesaPorSubcategoria]
    estrutura_custo_mensal: list[EstruturaCustoMes]
    caixinhas_patrimonio: list[SaldoCaixinha]
    retiradas_pendentes: list[Transacao]
