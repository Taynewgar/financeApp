import { useState } from 'react'
import './evolucaoChart.css'
import { escalaY } from '../lib/escala'
import { formatarMoeda } from '../lib/formatar'
import type { PontoEvolucaoMensal } from '../lib/types'

const LARGURA = 600
const ALTURA = 220
const MARGEM = { topo: 12, base: 28, esquerda: 52, direita: 12 }
const ALTURA_PLOT = ALTURA - MARGEM.topo - MARGEM.base

const MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  return `${MESES_ABREV[Number(mes) - 1]}/${ano.slice(2)}`
}

export function EvolucaoChart({ meses }: { meses: PontoEvolucaoMensal[] }) {
  const [indiceHover, setIndiceHover] = useState<number | null>(null)
  const [mostrarTabela, setMostrarTabela] = useState(false)

  if (meses.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Sem dados no período.</p>
  }

  const valores = meses.flatMap((m) => [m.receitas, m.despesas_brutas, m.resultado_saude, 0])
  const { min, max, marcacoes } = escalaY(valores)

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / meses.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - (valor - min) / (max - min || 1))
  const yBase = y(0)

  // barras agrupadas (Receita/Despesa) lado a lado dentro da banda do mês,
  // com um respiro de 2px entre elas (marks-and-anatomy: surface gap entre
  // marcas adjacentes)
  const grupoLargura = larguraBanda * 0.6
  const barraLargura = (grupoLargura - 2) / 2
  const xReceita = (i: number) => x(i) - grupoLargura / 2
  const xDespesa = (i: number) => xReceita(i) + barraLargura + 2
  const retanguloBarra = (valor: number) => ({
    y: Math.min(yBase, y(valor)),
    altura: Math.abs(yBase - y(valor)),
  })

  const linhaResultado = meses
    .map((m, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(m.resultado_saude).toFixed(1)}`)
    .join(' ')

  const hover = indiceHover !== null ? meses[indiceHover] : null

  return (
    <div className="evolucao-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-bloco serie-receitas" /> Receitas
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-bloco serie-despesas" /> Despesas
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha serie-resultado" /> Resultado
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
              <th>Receitas</th>
              <th>Despesas</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.vigencia_mes}>
                <td>{rotuloMes(m.vigencia_mes)}</td>
                <td>{formatarMoeda(m.receitas)}</td>
                <td>{formatarMoeda(m.despesas_brutas)}</td>
                <td>{formatarMoeda(m.resultado_saude)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="evolucao-chart-area">
          <svg
            viewBox={`0 0 ${LARGURA} ${ALTURA}`}
            role="img"
            aria-label="Evolução de receitas, despesas e resultado por mês"
          >
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
                <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {formatarMoeda(v).replace('R$', '').trim()}
                </text>
              </g>
            ))}

            {meses.map((m, i) => {
              const receita = retanguloBarra(m.receitas)
              const despesa = retanguloBarra(m.despesas_brutas)
              return (
                <g key={m.vigencia_mes}>
                  <rect
                    x={xReceita(i)}
                    y={receita.y}
                    width={barraLargura}
                    height={receita.altura}
                    rx={3}
                    fill="var(--serie-receitas)"
                  />
                  <rect
                    x={xDespesa(i)}
                    y={despesa.y}
                    width={barraLargura}
                    height={despesa.altura}
                    rx={3}
                    fill="var(--serie-despesas)"
                  />
                  <text x={x(i)} y={ALTURA - 8} className="evolucao-eixo-texto" textAnchor="middle">
                    {rotuloMes(m.vigencia_mes)}
                  </text>
                </g>
              )
            })}

            <path d={linhaResultado} className="evolucao-linha" fill="none" stroke="var(--serie-resultado)" />
            {meses.map((m, i) => (
              <circle
                key={m.vigencia_mes}
                cx={x(i)}
                cy={y(m.resultado_saude)}
                r={4}
                className="evolucao-marcador"
                fill="var(--serie-resultado)"
              />
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
                aria-label={`${rotuloMes(meses[i].vigencia_mes)}: receitas ${formatarMoeda(meses[i].receitas)}, despesas ${formatarMoeda(meses[i].despesas_brutas)}, resultado ${formatarMoeda(meses[i].resultado_saude)}`}
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
                <span className="evolucao-legenda-bloco serie-receitas" /> {formatarMoeda(hover.receitas)}
              </span>
              <span>
                <span className="evolucao-legenda-bloco serie-despesas" /> {formatarMoeda(hover.despesas_brutas)}
              </span>
              <span>
                <span className="evolucao-legenda-linha serie-resultado" /> {formatarMoeda(hover.resultado_saude)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
