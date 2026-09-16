import { useState } from 'react'
import './evolucaoChart.css'
import './taxaPoupancaChart.css'
import { escalaY } from '../lib/escala'
import { usePrivacidade } from '../lib/PrivacyContext'
import type { PontoEvolucaoMensal } from '../lib/types'

const LARGURA = 600
const ALTURA = 160
const MARGEM = { topo: 12, base: 28, esquerda: 44, direita: 12 }
const ALTURA_PLOT = ALTURA - MARGEM.topo - MARGEM.base

const MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  return `${MESES_ABREV[Number(mes) - 1]}/${ano.slice(2)}`
}

/** Taxa de poupança MENSAL (não a acumulada, que já aparece no Dashboard) —
 * gráfico próprio, de 1 série só, porque % e R$ não cabem no mesmo eixo
 * (regra "one axis" da skill de dataviz — nunca dual-axis). */
export function TaxaPoupancaChart({ meses }: { meses: PontoEvolucaoMensal[] }) {
  const { oculto } = usePrivacidade()
  const [indiceHover, setIndiceHover] = useState<number | null>(null)
  const [mostrarTabela, setMostrarTabela] = useState(false)

  if (meses.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Sem dados no período.</p>
  }

  const valores = meses.map((m) => m.taxa_poupanca).filter((v): v is number => v !== null)
  const { min, max, marcacoes } = escalaY(valores.length ? valores : [0])

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / meses.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - (valor - min) / (max - min || 1))

  // pula meses sem taxa (receita ajustada zero) em vez de interpolar —
  // "M" reabre o traço depois de um buraco (índice não contíguo ao ponto
  // válido anterior) em vez de ligar por cima dele
  const pontosValidos = meses
    .map((m, i) => (m.taxa_poupanca === null ? null : { i, valor: m.taxa_poupanca }))
    .filter((p): p is { i: number; valor: number } => p !== null)

  const linhaTaxa = pontosValidos
    .map((p, idx) => {
      const anterior = pontosValidos[idx - 1]
      const comando = idx === 0 || anterior.i !== p.i - 1 ? 'M' : 'L'
      return `${comando} ${x(p.i).toFixed(1)} ${y(p.valor).toFixed(1)}`
    })
    .join(' ')

  const hover = indiceHover !== null ? meses[indiceHover] : null

  return (
    <div className="taxa-poupanca-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha serie-taxa" /> Taxa de poupança mensal
          </span>
        </div>
        <button type="button" className="botao-link" onClick={() => setMostrarTabela((v) => !v)}>
          {mostrarTabela ? 'Ver gráfico' : 'Ver como tabela'}
        </button>
      </div>

      {mostrarTabela ? (
        <table className="evolucao-tabela">
          <thead>
            <tr>
              <th>Mês</th>
              <th>Taxa de poupança</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.vigencia_mes}>
                <td>{rotuloMes(m.vigencia_mes)}</td>
                <td>{m.taxa_poupanca === null ? '—' : `${m.taxa_poupanca.toFixed(1)}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="evolucao-chart-area">
          <svg
            viewBox={`0 0 ${LARGURA} ${ALTURA}`}
            role="img"
            aria-label="Taxa de poupança mensal, em percentual"
          >
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
                <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {oculto ? '•••' : `${v.toFixed(0)}%`}
                </text>
              </g>
            ))}

            {meses.map((m, i) => (
              <text key={m.vigencia_mes} x={x(i)} y={ALTURA - 8} className="evolucao-eixo-texto" textAnchor="middle">
                {rotuloMes(m.vigencia_mes)}
              </text>
            ))}

            <path d={linhaTaxa} className="evolucao-linha" fill="none" stroke="var(--serie-taxa)" />
            {meses.map(
              (m, i) =>
                m.taxa_poupanca !== null && (
                  <circle
                    key={m.vigencia_mes}
                    cx={x(i)}
                    cy={y(m.taxa_poupanca)}
                    r={4}
                    className="evolucao-marcador"
                    fill="var(--serie-taxa)"
                  />
                ),
            )}

            {indiceHover !== null && (
              <line
                x1={x(indiceHover)}
                x2={x(indiceHover)}
                y1={MARGEM.topo}
                y2={ALTURA - MARGEM.base}
                className="evolucao-crosshair"
              />
            )}

            {meses.map((_, i) => (
              <rect
                key={i}
                x={MARGEM.esquerda + larguraBanda * i}
                y={MARGEM.topo}
                width={larguraBanda}
                height={ALTURA_PLOT}
                fill="transparent"
                tabIndex={0}
                aria-label={
                  oculto
                    ? `${rotuloMes(meses[i].vigencia_mes)}: valor oculto`
                    : `${rotuloMes(meses[i].vigencia_mes)}: taxa de poupança ${meses[i].taxa_poupanca === null ? 'sem dados' : `${meses[i].taxa_poupanca!.toFixed(1)}%`}`
                }
                onMouseEnter={() => setIndiceHover(i)}
                onFocus={() => setIndiceHover(i)}
                onMouseLeave={() => setIndiceHover(null)}
                onBlur={() => setIndiceHover(null)}
              />
            ))}
          </svg>

          {hover && (
            <div className="evolucao-tooltip" style={{ left: `${(x(indiceHover!) / LARGURA) * 100}%` }}>
              <strong>{rotuloMes(hover.vigencia_mes)}</strong>
              <span>
                <span className="evolucao-legenda-linha serie-taxa" />{' '}
                {hover.taxa_poupanca === null ? 'Sem dados' : `${oculto ? '•••' : hover.taxa_poupanca.toFixed(1) + '%'}`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
