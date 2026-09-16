import { useEffect, useState } from 'react'
import { DespesasPorCategoria } from '../components/DespesasPorCategoria'
import { EvolucaoChart } from '../components/EvolucaoChart'
import { SeletorPeriodo } from '../components/SeletorPeriodo'
import { TaxaPoupancaChart } from '../components/TaxaPoupancaChart'
import '../components/forms.css'
import { ApiError, apiFetch } from '../lib/api'
import { mesesAntes, rotuloMesLongo, usePeriodo } from '../lib/periodo'
import type { DespesaPorCategoria as DespesaPorCategoriaT, EvolucaoMensal } from '../lib/types'

/** Toda visualização gráfica do app mora aqui — Dashboard fica só com
 * informação sintética (números/KPIs/sparkline). Ver docs/backlog.md
 * item 5 e o changelog (rodada 3/4 de 2026-09-15) pro racional completo
 * da divisão. */
export function Graficos() {
  const periodo = usePeriodo()
  const { modoData, vigenciaMes, periodoInicio, periodoFim, mesReferencia, primeiroMes } = periodo

  const [evolucao, setEvolucao] = useState<EvolucaoMensal | null>(null)
  const [despesasCategoria, setDespesasCategoria] = useState<DespesaPorCategoriaT[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (modoData === 'todos' && primeiroMes === null) return // aguarda carregar o início do histórico
    setErro(null)

    const evolucaoInicio = modoData === 'mes' ? mesesAntes(vigenciaMes, 5) : periodoInicio
    const evolucaoFim = periodoFim

    Promise.all([
      apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${evolucaoInicio}-01&fim=${evolucaoFim}-01`),
      apiFetch<DespesaPorCategoriaT[]>(`/dashboard/despesas-por-categoria/${mesReferencia}-01`),
    ])
      .then(([e, d]) => {
        setEvolucao(e)
        setDespesasCategoria(d)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar os gráficos'))
  }, [modoData, vigenciaMes, periodoInicio, periodoFim, mesReferencia, primeiroMes])

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 0 }}>Gráficos</h1>

      <SeletorPeriodo {...periodo} />

      {erro && <p className="mensagem-erro">{erro}</p>}

      {evolucao === null && !erro && <p>Carregando…</p>}

      {evolucao && (
        <div style={{ marginTop: 20, marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Evolução Mensal</h2>
          <EvolucaoChart meses={evolucao.meses} />
        </div>
      )}

      {evolucao && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Taxa de Poupança Mensal</h2>
          <TaxaPoupancaChart meses={evolucao.meses} />
        </div>
      )}

      {despesasCategoria && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Despesas por Categoria — {rotuloMesLongo(mesReferencia)}</h2>
          <DespesasPorCategoria dados={despesasCategoria} />
        </div>
      )}
    </div>
  )
}
