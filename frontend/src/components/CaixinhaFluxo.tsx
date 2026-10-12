import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoeda } from '../lib/formatar'
import { hojeAnoMes, mesesAntes } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, SerieMensal } from '../lib/types'

const LARG = 900
const ALT = 420
const MARG = { topo: 16, base: 32, esq: 64, dir: 16 }
const ALT_PLOT = ALT - MARG.topo - MARG.base
const MESES_JANELA = 12
const COR_APORTE = '#2dd4bf'
const COR_RETIRADA = '#f59e0b'

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
}

/** Item 51 do backlog — fluxo de uma caixinha: aporte x retirada mês a
 * mês, com linha de saldo acumulado no período sobreposta. */
export function CaixinhaFluxo() {
  const { oculto } = usePrivacidade()
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [caixinhaId, setCaixinhaId] = useState<string | null>(null)
  const [aporte, setAporte] = useState<SerieMensal | null>(null)
  const [retirada, setRetirada] = useState<SerieMensal | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const mesInicio = useMemo(() => mesesAntes(hojeAnoMes(), MESES_JANELA - 1), [])
  const mesFim = useMemo(() => hojeAnoMes(), [])

  useEffect(() => {
    apiFetch<Caixinha[]>('/caixinhas')
      .then((r) => {
        const ativas = r.filter((c) => c.ativo)
        setCaixinhas(ativas)
        if (ativas.length > 0) setCaixinhaId(ativas[0].id)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!caixinhaId) return
    const params = new URLSearchParams({ inicio: `${mesInicio}-01`, fim: `${mesFim}-01` })
    params.append('series', `caixinha_aporte:${caixinhaId}`)
    params.append('series', `caixinha_retirada:${caixinhaId}`)
    apiFetch<SerieMensal[]>(`/dashboard/series-mensais?${params.toString()}`)
      .then((r) => {
        setAporte(r.find((s) => s.chave === `caixinha_aporte:${caixinhaId}`) ?? null)
        setRetirada(r.find((s) => s.chave === `caixinha_retirada:${caixinhaId}`) ?? null)
        setErro(null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o fluxo da caixinha'))
  }, [caixinhaId, mesInicio, mesFim])

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

  const espacamento = meses.length > 1 ? (LARG - MARG.esq - MARG.dir) / (meses.length - 1) : 0
  const x = (i: number) => (meses.length > 1 ? MARG.esq + espacamento * i : MARG.esq)
  const y = (v: number) => MARG.topo + ALT_PLOT * (1 - (v - min) / (max - min || 1))
  const yBase = y(0)

  const grupoLargura = espacamento * 0.72
  const larguraBarra = Math.max(2, (grupoLargura - 2) / 2)

  return (
    <div>
      <div className="comparador-controles">
        {caixinhas.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`botao-chip ${caixinhaId === c.id ? 'ativo' : ''}`}
            onClick={() => setCaixinhaId(c.id)}
          >
            {c.nome}
          </button>
        ))}
      </div>

      {erro && <p className="mensagem-erro">{erro}</p>}

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

        {aporte && retirada && meses.length > 0 && (
          <svg viewBox={`0 0 ${LARG} ${ALT}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Fluxo de aporte e retirada da caixinha">
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARG.esq} x2={LARG - MARG.dir} y1={y(v)} y2={y(v)} className="comparador-grade" />
                <text x={MARG.esq - 8} y={y(v)} className="comparador-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {oculto ? '•••' : formatarMoeda(v).replace('R$', '').trim()}
                </text>
              </g>
            ))}
            {meses.map((m, i) => (
              <text key={m} x={x(i)} y={ALT - 10} className="comparador-eixo-texto" textAnchor="middle">
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
        )}
      </div>
    </div>
  )
}
