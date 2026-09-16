import { useEffect, useState } from 'react'
import { DespesasPorCategoria } from '../components/DespesasPorCategoria'
import { EvolucaoChart } from '../components/EvolucaoChart'
import { Pareto } from '../components/Pareto'
import { SeletorPeriodo } from '../components/SeletorPeriodo'
import { TaxaPoupancaChart } from '../components/TaxaPoupancaChart'
import '../components/forms.css'
import { ApiError, apiFetch } from '../lib/api'
import { mesesAntes, rotuloMesLongo, usePeriodo } from '../lib/periodo'
import type {
  Categoria,
  DespesaPorCategoria as DespesaPorCategoriaT,
  DespesaPorSubcategoria,
  EvolucaoMensal,
} from '../lib/types'

type NivelPareto = 'categoria' | 'subcategoria'

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

  const [nivelPareto, setNivelPareto] = useState<NivelPareto>('categoria')
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [categoriasDespesa, setCategoriasDespesa] = useState<Categoria[]>([])
  const [paretoSubcategoria, setParetoSubcategoria] = useState<DespesaPorSubcategoria[] | null>(null)
  const [erroPareto, setErroPareto] = useState<string | null>(null)

  // categorias de despesa pro filtro "categoria pai" do Pareto de
  // subcategoria — não depende do período navegado
  useEffect(() => {
    apiFetch<Categoria[]>('/categorias?tipo=despesa').then(setCategoriasDespesa).catch(() => setCategoriasDespesa([]))
  }, [])

  useEffect(() => {
    if (modoData === 'todos' && primeiroMes === null) return // aguarda carregar o início do histórico
    setErro(null)

    // tela dedicada de análise — janela maior que o sparkline do Dashboard
    // (6 meses); 12 meses dá leitura de trailing-year no modo "Mês"
    const evolucaoInicio = modoData === 'mes' ? mesesAntes(vigenciaMes, 11) : periodoInicio
    const evolucaoFim = periodoFim

    // "Mês" olha só o mês de referência; Intervalo/Todos somam o período
    // inteiro, não só o último mês (mesmo padrão de /mensal vs /resumo-periodo)
    const buscaDespesasCategoria =
      modoData === 'mes'
        ? apiFetch<DespesaPorCategoriaT[]>(`/dashboard/despesas-por-categoria/${mesReferencia}-01`)
        : apiFetch<DespesaPorCategoriaT[]>(
            `/dashboard/despesas-por-categoria-periodo?inicio=${periodoInicio}-01&fim=${periodoFim}-01`,
          )

    Promise.all([
      apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${evolucaoInicio}-01&fim=${evolucaoFim}-01`),
      buscaDespesasCategoria,
    ])
      .then(([e, d]) => {
        setEvolucao(e)
        setDespesasCategoria(d)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar os gráficos'))
  }, [modoData, vigenciaMes, periodoInicio, periodoFim, mesReferencia, primeiroMes])

  // Pareto por categoria reaproveita despesasCategoria (mesmo endpoint já
  // buscado acima pro gráfico "Despesas por Categoria") — só o nível
  // subcategoria precisa de busca própria, porque depende também do
  // filtro de categoria pai
  useEffect(() => {
    if (nivelPareto !== 'subcategoria') return
    if (modoData === 'todos' && primeiroMes === null) return
    setErroPareto(null)

    const filtroQuery = categoriaFiltro ? `categoria_id=${categoriaFiltro}` : ''
    const busca =
      modoData === 'mes'
        ? apiFetch<DespesaPorSubcategoria[]>(`/dashboard/despesas-por-subcategoria/${mesReferencia}-01?${filtroQuery}`)
        : apiFetch<DespesaPorSubcategoria[]>(
            `/dashboard/despesas-por-subcategoria-periodo?inicio=${periodoInicio}-01&fim=${periodoFim}-01&${filtroQuery}`,
          )

    busca
      .then(setParetoSubcategoria)
      .catch((e) => setErroPareto(e instanceof ApiError ? e.message : 'Falha ao carregar o Pareto'))
  }, [nivelPareto, categoriaFiltro, modoData, mesReferencia, periodoInicio, periodoFim, primeiroMes])

  const itensPareto =
    nivelPareto === 'categoria'
      ? (despesasCategoria ?? []).map((d) => ({ id: d.categoria_id, nome: d.categoria_nome, valor: d.valor, percentual: d.percentual }))
      : (paretoSubcategoria ?? []).map((d) => ({
          id: d.subcategoria_id ?? '_sem_subcategoria',
          nome: d.subcategoria_nome,
          valor: d.valor,
          percentual: d.percentual,
        }))

  const carregandoPareto = nivelPareto === 'categoria' ? despesasCategoria === null : paretoSubcategoria === null

  const rotuloPeriodoDespesas =
    modoData === 'mes' ? rotuloMesLongo(mesReferencia) : `${rotuloMesLongo(periodoInicio)} a ${rotuloMesLongo(periodoFim)}`

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 0 }}>Gráficos</h1>

      <SeletorPeriodo {...periodo} />

      {erro && <p className="mensagem-erro">{erro}</p>}

      <div style={{ marginTop: 20, marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, marginBottom: 8 }}>Pareto de Despesas — {rotuloPeriodoDespesas}</h2>
        <div className="campo-linha" style={{ marginBottom: 10, alignItems: 'flex-end' }}>
          <div className="segmentado">
            <button
              type="button"
              className={nivelPareto === 'categoria' ? 'ativo' : ''}
              onClick={() => setNivelPareto('categoria')}
            >
              Por categoria
            </button>
            <button
              type="button"
              className={nivelPareto === 'subcategoria' ? 'ativo' : ''}
              onClick={() => setNivelPareto('subcategoria')}
            >
              Por subcategoria
            </button>
          </div>
          {nivelPareto === 'subcategoria' && (
            <label className="campo" style={{ maxWidth: 220 }}>
              Categoria pai
              <select value={categoriaFiltro} onChange={(e) => setCategoriaFiltro(e.target.value)}>
                <option value="">Todas</option>
                {categoriasDespesa.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {erroPareto && <p className="mensagem-erro">{erroPareto}</p>}
        {carregandoPareto ? <p>Carregando…</p> : <Pareto itens={itensPareto} />}
      </div>

      {evolucao === null && !erro && <p>Carregando…</p>}

      {evolucao && (
        <div style={{ marginTop: 20, marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Evolução Mensal</h2>
          <EvolucaoChart meses={evolucao.meses} baseMedia={periodo.baseMedia} />
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--cor-texto-suave)', margin: '18px 0 8px' }}>
            Taxa de poupança mensal
          </h3>
          <TaxaPoupancaChart meses={evolucao.meses} baseMedia={periodo.baseMedia} />
        </div>
      )}

      {despesasCategoria && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Despesas por Categoria — {rotuloPeriodoDespesas}</h2>
          <DespesasPorCategoria dados={despesasCategoria} />
        </div>
      )}
    </div>
  )
}
