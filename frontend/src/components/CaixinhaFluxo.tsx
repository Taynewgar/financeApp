import { useEffect, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { corDaSerie } from '../lib/coresSeries'
import { formatarMoeda } from '../lib/formatar'
import { calcularPeriodoGrafico, hojeAnoMes, PERIODOS_GRAFICO } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, SerieMensal } from '../lib/types'

const LARG = 900
const COR_APORTE = '#2dd4bf'
const COR_RETIRADA = '#f59e0b'

type ModoAgregacao = 'porCaixinha' | 'somado'

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
}

/** 1 caixinha marcada: gráfico detalhado — aporte x retirada mês a mês +
 * saldo acumulado sobreposto. Não tem problema de "como combinar várias"
 * (é só 1), então mantém o nível de detalhe original. */
function FluxoChart({ aporte, retirada, oculto }: { aporte: SerieMensal | null; retirada: SerieMensal | null; oculto: boolean }) {
  const alt = 300
  const marg = { topo: 14, base: 28, esq: 64, dir: 16 }
  const altPlot = alt - marg.topo - marg.base

  const meses = aporte ? aporte.pontos.map((p) => p.vigencia_mes) : []
  const saldoAcumulado: number[] = []
  if (aporte && retirada) {
    let acumulado = 0
    aporte.pontos.forEach((p, i) => {
      acumulado += p.valor - retirada.pontos[i].valor
      saldoAcumulado.push(acumulado)
    })
  }

  const todosValores = [
    ...(aporte?.pontos.map((p) => p.valor) ?? []),
    ...(retirada?.pontos.map((p) => p.valor) ?? []),
    ...saldoAcumulado,
  ]
  const { min, max, marcacoes } = escalaY(todosValores)

  const espacamento = meses.length > 1 ? (LARG - marg.esq - marg.dir) / (meses.length - 1) : 0
  const x = (i: number) => (meses.length > 1 ? marg.esq + espacamento * i : marg.esq)
  const y = (v: number) => marg.topo + altPlot * (1 - (v - min) / (max - min || 1))
  const yBase = y(0)

  const grupoLargura = espacamento * 0.72
  const larguraBarra = Math.max(2, (grupoLargura - 2) / 2)

  if (!aporte || !retirada || meses.length === 0) return null

  return (
    <div className="comparador-chart-card">
      <div className="comparador-legenda">
        <span className="comparador-legenda-item">
          <span className="comparador-chip-cor" style={{ background: COR_APORTE }} />
          Aporte
        </span>
        <span className="comparador-legenda-item">
          <span className="comparador-chip-cor" style={{ background: COR_RETIRADA }} />
          Retirada
        </span>
        <span className="comparador-legenda-item">
          <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: '2px solid var(--cor-texto)' }} />
          Saldo acumulado no período
        </span>
      </div>

      <svg viewBox={`0 0 ${LARG} ${alt}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Fluxo de aporte e retirada da caixinha">
        {marcacoes.map((v) => (
          <g key={v}>
            <line x1={marg.esq} x2={LARG - marg.dir} y1={y(v)} y2={y(v)} className="comparador-grade" />
            <text x={marg.esq - 8} y={y(v)} className="comparador-eixo-texto" textAnchor="end" dominantBaseline="middle">
              {oculto ? '•••' : formatarMoeda(v).replace('R$', '').trim()}
            </text>
          </g>
        ))}
        {meses.map((m, i) => (
          <text key={m} x={x(i)} y={alt - 10} className="comparador-eixo-texto" textAnchor="middle">
            {rotuloMes(m)}
          </text>
        ))}

        {meses.map((_, i) => {
          const vAporte = aporte.pontos[i].valor
          const vRetirada = retirada.pontos[i].valor
          const xAporte = x(i) - grupoLargura / 2
          const xRetirada = xAporte + larguraBarra + 2
          return (
            <g key={i}>
              <rect
                x={xAporte}
                y={Math.min(yBase, y(vAporte))}
                width={larguraBarra}
                height={Math.abs(yBase - y(vAporte))}
                rx={2}
                fill={COR_APORTE}
              />
              <rect
                x={xRetirada}
                y={Math.min(yBase, y(vRetirada))}
                width={larguraBarra}
                height={Math.abs(yBase - y(vRetirada))}
                rx={2}
                fill={COR_RETIRADA}
              />
            </g>
          )
        })}

        <path
          d={saldoAcumulado.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')}
          fill="none"
          stroke="var(--cor-texto)"
          strokeWidth={2.5}
        />
        {saldoAcumulado.map((v, i) => (
          <circle key={i} cx={x(i)} cy={y(v)} r={3.5} fill="var(--cor-texto)" />
        ))}
      </svg>
    </div>
  )
}

/** 2+ caixinhas marcadas: 1 gráfico só, barras de FLUXO LÍQUIDO (aporte −
 * retirada do mês, pode ficar negativo) — opção escolhida pelo usuário
 * num mockup (Rodada 100) entre 3 formas de combinar várias caixinhas
 * num gráfico. "Por caixinha" agrupa 1 barra por caixinha; "Somado"
 * soma o líquido de todas as marcadas numa barra só por mês. */
function FluxoLiquidoChart({
  caixinhasSelecionadas,
  series,
  modoAgregacao,
  oculto,
}: {
  caixinhasSelecionadas: Caixinha[]
  series: SerieMensal[]
  modoAgregacao: ModoAgregacao
  oculto: boolean
}) {
  const alt = 300
  const marg = { topo: 14, base: 28, esq: 64, dir: 16 }
  const altPlot = alt - marg.topo - marg.base

  const meses = series.length > 0 ? series[0].pontos.map((p) => p.vigencia_mes) : []

  const liquidoPorCaixinha = caixinhasSelecionadas.map((c) => {
    const aporte = series.find((s) => s.chave === `caixinha_aporte:${c.id}`)
    const retirada = series.find((s) => s.chave === `caixinha_retirada:${c.id}`)
    const liquido = meses.map((_, i) => (aporte?.pontos[i]?.valor ?? 0) - (retirada?.pontos[i]?.valor ?? 0))
    return { caixinha: c, liquido }
  })
  const liquidoSomado = meses.map((_, i) => liquidoPorCaixinha.reduce((acc, p) => acc + p.liquido[i], 0))

  const todosValores = modoAgregacao === 'somado' ? liquidoSomado : liquidoPorCaixinha.flatMap((p) => p.liquido)
  const { min, max, marcacoes } = escalaY(todosValores)

  const espacamento = meses.length > 1 ? (LARG - marg.esq - marg.dir) / (meses.length - 1) : 0
  const x = (i: number) => (meses.length > 1 ? marg.esq + espacamento * i : marg.esq)
  const y = (v: number) => marg.topo + altPlot * (1 - (v - min) / (max - min || 1))
  const yBase = y(0)

  const grupoLargura = espacamento * 0.78
  const totalBarras = modoAgregacao === 'somado' ? 1 : liquidoPorCaixinha.length
  const larguraBarra = Math.max(2, (grupoLargura - (totalBarras - 1) * 2) / totalBarras)

  if (meses.length === 0) return null

  return (
    <div className="comparador-chart-card">
      <div className="comparador-legenda">
        {modoAgregacao === 'porCaixinha' ? (
          caixinhasSelecionadas.map((c, i) => (
            <span key={c.id} className="comparador-legenda-item">
              <span className="comparador-chip-cor" style={{ background: corDaSerie(i) }} />
              {c.nome}
            </span>
          ))
        ) : (
          <span className="comparador-legenda-item">
            <span className="comparador-chip-cor" style={{ background: 'var(--cor-acento)' }} />
            Fluxo líquido somado ({caixinhasSelecionadas.length} caixinhas)
          </span>
        )}
      </div>

      <svg viewBox={`0 0 ${LARG} ${alt}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Fluxo líquido das caixinhas marcadas">
        {marcacoes.map((v) => (
          <g key={v}>
            <line x1={marg.esq} x2={LARG - marg.dir} y1={y(v)} y2={y(v)} className="comparador-grade" />
            <text x={marg.esq - 8} y={y(v)} className="comparador-eixo-texto" textAnchor="end" dominantBaseline="middle">
              {oculto ? '•••' : formatarMoeda(v).replace('R$', '').trim()}
            </text>
          </g>
        ))}
        {meses.map((m, i) => (
          <text key={m} x={x(i)} y={alt - 10} className="comparador-eixo-texto" textAnchor="middle">
            {rotuloMes(m)}
          </text>
        ))}

        {modoAgregacao === 'porCaixinha' &&
          meses.map((_, i) => {
            const centro = x(i)
            return liquidoPorCaixinha.map((p, k) => {
              const v = p.liquido[i]
              const xBarra = centro - grupoLargura / 2 + k * (larguraBarra + 2)
              const yTopo = Math.min(yBase, y(v))
              return <rect key={p.caixinha.id} x={xBarra} y={yTopo} width={larguraBarra} height={Math.abs(yBase - y(v))} rx={2} fill={corDaSerie(k)} />
            })
          })}

        {modoAgregacao === 'somado' &&
          meses.map((m, i) => {
            const v = liquidoSomado[i]
            const xBarra = x(i) - larguraBarra / 2
            const yTopo = Math.min(yBase, y(v))
            return <rect key={m} x={xBarra} y={yTopo} width={larguraBarra} height={Math.abs(yBase - y(v))} rx={2} fill="var(--cor-acento)" />
          })}

        {/* linha do zero em destaque — com valor líquido negativo é
         * importante deixar claro onde a barra "vira" */}
        <line x1={marg.esq} x2={LARG - marg.dir} y1={yBase} y2={yBase} stroke="var(--cor-texto-suave)" strokeWidth={1} />
      </svg>
    </div>
  )
}

/** Item 51/91/98 do backlog — fluxo de caixinha. Rodada 91: ganhou
 * multi-seleção (antes só 1 caixinha por vez). Rodada 100: a forma de
 * combinar várias caixinhas num gráfico só virou fluxo líquido (aporte
 * − retirada do mês, por caixinha), escolhida pelo usuário num mockup
 * entre 3 opções — antes "Separado" virava 1 card por caixinha, decisão
 * que o usuário não esperava/não gostou. */
export function CaixinhaFluxo() {
  const { oculto } = usePrivacidade()
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set())
  const [modoAgregacao, setModoAgregacao] = useState<ModoAgregacao>('porCaixinha')
  const [periodoIndice, setPeriodoIndice] = useState(1)
  const [series, setSeries] = useState<SerieMensal[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<Caixinha[]>('/caixinhas')
      .then((r) => {
        const ativas = r.filter((c) => c.ativo)
        setCaixinhas(ativas)
        if (ativas.length > 0) setSelecionadas(new Set([ativas[0].id]))
      })
      .catch(() => {})
  }, [])

  function alternar(id: string) {
    setSelecionadas((atual) => {
      const novo = new Set(atual)
      if (novo.has(id)) novo.delete(id)
      else novo.add(id)
      return novo
    })
  }

  const [mesFim] = useState(() => hojeAnoMes())
  const { inicio: mesInicio } = calcularPeriodoGrafico(periodoIndice, mesFim)

  useEffect(() => {
    if (selecionadas.size === 0) {
      setSeries([])
      return
    }
    const params = new URLSearchParams({ inicio: `${mesInicio}-01`, fim: `${mesFim}-01` })
    selecionadas.forEach((id) => {
      params.append('series', `caixinha_aporte:${id}`)
      params.append('series', `caixinha_retirada:${id}`)
    })
    apiFetch<SerieMensal[]>(`/dashboard/series-mensais?${params.toString()}`)
      .then((r) => {
        setSeries(r)
        setErro(null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o fluxo da caixinha'))
  }, [selecionadas, mesInicio, mesFim])

  const caixinhasSelecionadas = caixinhas.filter((c) => selecionadas.has(c.id))

  return (
    <div>
      <div className="comparador-controles">
        {caixinhas.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`botao-chip ${selecionadas.has(c.id) ? 'ativo' : ''}`}
            onClick={() => alternar(c.id)}
          >
            {c.nome}
          </button>
        ))}
      </div>

      <div className="comparador-controles">
        <button type="button" className="botao-chip" onClick={() => setPeriodoIndice((i) => (i + 1) % PERIODOS_GRAFICO.length)}>
          📅 {PERIODOS_GRAFICO[periodoIndice].label} ▾
        </button>
        {caixinhasSelecionadas.length >= 2 && (
          <>
            <button
              type="button"
              className={`botao-chip ${modoAgregacao === 'porCaixinha' ? 'ativo' : ''}`}
              onClick={() => setModoAgregacao('porCaixinha')}
            >
              ▥ Por caixinha
            </button>
            <button
              type="button"
              className={`botao-chip ${modoAgregacao === 'somado' ? 'ativo' : ''}`}
              onClick={() => setModoAgregacao('somado')}
            >
              Σ Somado
            </button>
          </>
        )}
      </div>

      {erro && <p className="mensagem-erro">{erro}</p>}
      {selecionadas.size === 0 && (
        <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13 }}>Marque ao menos uma caixinha acima.</p>
      )}

      {series && caixinhasSelecionadas.length === 1 && (
        <FluxoChart
          aporte={series.find((s) => s.chave === `caixinha_aporte:${caixinhasSelecionadas[0].id}`) ?? null}
          retirada={series.find((s) => s.chave === `caixinha_retirada:${caixinhasSelecionadas[0].id}`) ?? null}
          oculto={oculto}
        />
      )}

      {series && caixinhasSelecionadas.length >= 2 && (
        <FluxoLiquidoChart
          caixinhasSelecionadas={caixinhasSelecionadas}
          series={series}
          modoAgregacao={modoAgregacao}
          oculto={oculto}
        />
      )}
    </div>
  )
}
