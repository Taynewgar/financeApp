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

  const valores = meses.flatMap((m) => [m.receitas, m.despesas_liquidas, m.resultado_saude])
  const { min, max, marcacoes } = escalaY(valores)

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / meses.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - (valor - min) / (max - min || 1))

  const linha = (chave: 'receitas' | 'despesas_liquidas' | 'resultado_saude') =>
    meses.map((m, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(m[chave]).toFixed(1)}`).join(' ')

  const hover = indiceHover !== null ? meses[indiceHover] : null

  return (
    <div className="evolucao-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha serie-receitas" /> Receitas
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha serie-despesas" /> Despesas líquidas
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
              <th>Despesas líquidas</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.vigencia_mes}>
                <td>{rotuloMes(m.vigencia_mes)}</td>
                <td>{formatarMoeda(m.receitas)}</td>
                <td>{formatarMoeda(m.despesas_liquidas)}</td>
                <td>{formatarMoeda(m.resultado_saude)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="evolucao-chart-area">
          <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} role="img" aria-label="Evolução de receitas, despesas líquidas e resultado por mês">
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
                <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {formatarMoeda(v).replace('R$', '').trim()}
                </text>
              </g>
            ))}

            <path d={linha('receitas')} className="evolucao-linha" fill="none" stroke="var(--serie-receitas)" />
            <path d={linha('despesas_liquidas')} className="evolucao-linha" fill="none" stroke="var(--serie-despesas)" />
            <path d={linha('resultado_saude')} className="evolucao-linha" fill="none" stroke="var(--serie-resultado)" />

            {meses.map((m, i) => (
              <g key={m.vigencia_mes}>
                <circle cx={x(i)} cy={y(m.receitas)} r={4} className="evolucao-marcador" fill="var(--serie-receitas)" />
                <circle cx={x(i)} cy={y(m.despesas_liquidas)} r={4} className="evolucao-marcador" fill="var(--serie-despesas)" />
                <circle cx={x(i)} cy={y(m.resultado_saude)} r={4} className="evolucao-marcador" fill="var(--serie-resultado)" />
                <text x={x(i)} y={ALTURA - 8} className="evolucao-eixo-texto" textAnchor="middle">
                  {rotuloMes(m.vigencia_mes)}
                </text>
              </g>
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
                aria-label={`${rotuloMes(meses[i].vigencia_mes)}: receitas ${formatarMoeda(meses[i].receitas)}, despesas líquidas ${formatarMoeda(meses[i].despesas_liquidas)}, resultado ${formatarMoeda(meses[i].resultado_saude)}`}
                onMouseEnter={() => setIndiceHover(i)}
                onFocus={() => setIndiceHover(i)}
                onMouseLeave={() => setIndiceHover(null)}
                onBlur={() => setIndiceHover(null)}
              />
            ))}
          </svg>

          {hover && (
            <div
              className="evolucao-tooltip"
              style={{ left: `${(x(indiceHover!) / LARGURA) * 100}%` }}
            >
              <strong>{rotuloMes(hover.vigencia_mes)}</strong>
              <span>
                <span className="evolucao-legenda-linha serie-receitas" /> {formatarMoeda(hover.receitas)}
              </span>
              <span>
                <span className="evolucao-legenda-linha serie-despesas" /> {formatarMoeda(hover.despesas_liquidas)}
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
