import { useState } from 'react'
import './evolucaoChart.css'
import './percentualExecutadoChart.css'
import { escalaY } from '../lib/escala'
import { usePrivacidade } from '../lib/PrivacyContext'
import type { PontoTendenciaOrcamento } from '../lib/types'

const LARGURA = 600
const ALTURA = 160
const MARGEM = { topo: 12, base: 28, esquerda: 44, direita: 12 }
const ALTURA_PLOT = ALTURA - MARGEM.topo - MARGEM.base
const META = 100

const MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  return `${MESES_ABREV[Number(mes) - 1]}/${ano.slice(2)}`
}

/** % do orçado que foi de fato gasto, mês a mês — gráfico próprio (mesma
 * regra "one axis" das outras telas: já está em %, mas fica separado do
 * Orçado×Realizado em R$ pra não misturar duas leituras na mesma barra).
 * Linha de referência em 100% = "gastou exatamente o orçado" (meta fixa,
 * não uma média — diferente da linha de "Base da média" dos outros
 * gráficos). */
export function PercentualExecutadoChart({ meses }: { meses: PontoTendenciaOrcamento[] }) {
  const { oculto } = usePrivacidade()
  const [indiceHover, setIndiceHover] = useState<number | null>(null)
  const [mostrarTabela, setMostrarTabela] = useState(false)

  if (meses.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Sem dados no período.</p>
  }

  const valores = meses.map((m) => m.percentual_executado).filter((v): v is number => v !== null)
  const { min, max, marcacoes } = escalaY(valores.length ? [...valores, META] : [0, META])

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / meses.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - (valor - min) / (max - min || 1))
  const yBase = y(0)

  const barraLargura = larguraBanda * 0.5
  const retanguloBarra = (valor: number) => ({
    y: Math.min(yBase, y(valor)),
    altura: Math.abs(yBase - y(valor)),
  })

  const hover = indiceHover !== null ? meses[indiceHover] : null

  return (
    <div className="percentual-executado-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha-tracejada" style={{ color: 'var(--cor-texto-suave)' }} /> Meta (100%)
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
              <th>% executado</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.vigencia_mes}>
                <td>{rotuloMes(m.vigencia_mes)}</td>
                <td>{m.percentual_executado === null ? '—' : `${m.percentual_executado.toFixed(1)}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="evolucao-chart-area">
          <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} role="img" aria-label="Percentual do orçado executado, por mês">
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
                <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {oculto ? '•••' : `${v.toFixed(0)}%`}
                </text>
              </g>
            ))}

            <line
              x1={MARGEM.esquerda}
              x2={LARGURA - MARGEM.direita}
              y1={y(META)}
              y2={y(META)}
              className="evolucao-linha-media"
              stroke="var(--cor-texto-suave)"
            />

            {meses.map((m, i) => {
              if (m.percentual_executado === null) return null
              const barra = retanguloBarra(m.percentual_executado)
              return (
                <rect
                  key={m.vigencia_mes}
                  x={x(i) - barraLargura / 2}
                  y={barra.y}
                  width={barraLargura}
                  height={barra.altura}
                  rx={3}
                  fill="var(--serie-executado)"
                />
              )
            })}
            {meses.map((m, i) => (
              <text key={m.vigencia_mes} x={x(i)} y={ALTURA - 8} className="evolucao-eixo-texto" textAnchor="middle">
                {rotuloMes(m.vigencia_mes)}
              </text>
            ))}

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
                    : `${rotuloMes(meses[i].vigencia_mes)}: ${meses[i].percentual_executado === null ? 'sem orçamento' : `${meses[i].percentual_executado!.toFixed(1)}% executado`}`
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
                <span className="evolucao-legenda-bloco serie-executado" />{' '}
                {hover.percentual_executado === null
                  ? 'Sem orçamento'
                  : `${oculto ? '•••' : hover.percentual_executado.toFixed(1) + '%'}`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
