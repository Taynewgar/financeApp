import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoeda } from '../lib/formatar'
import { calcularPeriodoGrafico, hojeAnoMes, PERIODOS_GRAFICO } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, SerieMensal } from '../lib/types'

const LARG = 900
const COR_APORTE = '#2dd4bf'
const COR_RETIRADA = '#f59e0b'

type ModoAgregacao = 'separado' | 'somado'

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
}

function somarSeries(series: SerieMensal[], chaves: string[], meses: string[]): SerieMensal {
  const pontos = meses.map((m, i) => ({
    vigencia_mes: m,
    valor: chaves.reduce((acc, chave) => acc + (series.find((s) => s.chave === chave)?.pontos[i]?.valor ?? 0), 0),
  }))
  return { chave: 'somado', nome: 'Somado', pontos }
}

/** 1 gráfico de fluxo (aporte × retirada + saldo acumulado) — usado tanto
 * pro modo "Separado" (1 instância compacta por caixinha marcada) quanto
 * pro "Somado" (1 instância cheia, com os totais agregados). */
function FluxoChart({
  aporte,
  retirada,
  titulo,
  compacto,
  oculto,
}: {
  aporte: SerieMensal | null
  retirada: SerieMensal | null
  titulo?: string
  compacto?: boolean
  oculto: boolean
}) {
  const alt = compacto ? 260 : 420
  const marg = { topo: 16, base: 32, esq: 64, dir: 16 }
  const altPlot = alt - marg.topo - marg.base

  const meses = aporte ? aporte.pontos.map((p) => p.vigencia_mes) : []
  const saldoAcumulado = useMemo(() => {
    if (!aporte || !retirada) return []
    let acumulado = 0
    return aporte.pontos.map((p, i) => {
      acumulado += p.valor - retirada.pontos[i].valor
      return acumulado
    })
  }, [aporte, retirada])

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
      {titulo && <div className="comparador-fluxo-titulo">{titulo}</div>}
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

/** Item 51/91 do backlog — fluxo de caixinha: aporte x retirada mês a
 * mês, com linha de saldo acumulado no período sobreposta. Rodada 91:
 * ganhou multi-seleção (antes só 1 caixinha por vez) com modo Separado
 * (1 mini-gráfico por caixinha) ou Somado (totais agregados num gráfico
 * só) e seletor de período próprio, igual aos outros 3 gráficos novos. */
export function CaixinhaFluxo() {
  const { oculto } = usePrivacidade()
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set())
  const [modoAgregacao, setModoAgregacao] = useState<ModoAgregacao>('separado')
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

  const meses = series && series.length > 0 ? series[0].pontos.map((p) => p.vigencia_mes) : []
  const caixinhasSelecionadas = caixinhas.filter((c) => selecionadas.has(c.id))

  const somado = useMemo(() => {
    if (!series || meses.length === 0 || caixinhasSelecionadas.length === 0) return null
    const chavesAporte = caixinhasSelecionadas.map((c) => `caixinha_aporte:${c.id}`)
    const chavesRetirada = caixinhasSelecionadas.map((c) => `caixinha_retirada:${c.id}`)
    return {
      aporte: somarSeries(series, chavesAporte, meses),
      retirada: somarSeries(series, chavesRetirada, meses),
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [series, meses.join(','), caixinhasSelecionadas.map((c) => c.id).join(',')])

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
              className={`botao-chip ${modoAgregacao === 'separado' ? 'ativo' : ''}`}
              onClick={() => setModoAgregacao('separado')}
            >
              ⬍ Separado
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

      {series && modoAgregacao === 'somado' && somado && (
        <FluxoChart
          aporte={somado.aporte}
          retirada={somado.retirada}
          titulo={`Somado (${caixinhasSelecionadas.length} caixinhas)`}
          oculto={oculto}
        />
      )}

      {series && modoAgregacao === 'separado' && (
        <div className={caixinhasSelecionadas.length > 1 ? 'comparador-fluxo-grid' : undefined}>
          {caixinhasSelecionadas.map((c) => (
            <FluxoChart
              key={c.id}
              aporte={series.find((s) => s.chave === `caixinha_aporte:${c.id}`) ?? null}
              retirada={series.find((s) => s.chave === `caixinha_retirada:${c.id}`) ?? null}
              titulo={caixinhasSelecionadas.length > 1 ? c.nome : undefined}
              compacto={caixinhasSelecionadas.length > 1}
              oculto={oculto}
            />
          ))}
        </div>
      )}
    </div>
  )
}
