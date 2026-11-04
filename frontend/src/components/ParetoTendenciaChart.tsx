import { useState } from 'react'
import './evolucaoChart.css'
import './paretoTendenciaChart.css'
import { formatarMoeda } from '../lib/formatar'
import { usePrivacidade } from '../lib/PrivacyContext'

type ItemPareto = { id: string; nome: string; valor: number; percentual: number }

const LARGURA = 600
const ALTURA = 140
const MARGEM = { topo: 12, base: 16, esquerda: 40, direita: 12 }
const ALTURA_PLOT = ALTURA - MARGEM.topo - MARGEM.base
const CORTE = 80
const MARCACOES = [0, 20, 40, 60, 80, 100]

/** Curva de % acumulado do Pareto — complementa a tabela de barras
 * horizontais (Pareto.tsx) mostrando o "cotovelo": onde o ganho marginal de
 * cada categoria adicional despenca. Sem rótulo de categoria no eixo X
 * (mesmo motivo da tabela ir horizontal: nome colide) — a ordem (rank) já é
 * a mesma da tabela logo abaixo, o hover nomeia a categoria. Eixo Y fixo
 * 0–100%, com linha tracejada em 80% marcando o critério clássico de
 * Pareto — mesmo padrão de "meta fixa" do PercentualExecutadoChart, não uma
 * média (Base da média não se aplica aqui, não é uma série temporal). */
export function ParetoTendenciaChart({ itens }: { itens: ItemPareto[] }) {
  const { oculto } = usePrivacidade()
  const [indiceHover, setIndiceHover] = useState<number | null>(null)

  if (itens.length === 0) return null

  // acumulado ANTES de cada item — mesmo padrão de Pareto.tsx (reduce em
  // vez de mutar variável externa ao map)
  const acumuladosAntes = itens.reduce<number[]>((acc, _item, i) => {
    acc.push(i === 0 ? 0 : acc[i - 1] + itens[i - 1].percentual)
    return acc
  }, [])
  const linhas = itens.map((item, i) => ({
    ...item,
    percentualAcumulado: Math.min(acumuladosAntes[i] + item.percentual, 100),
  }))

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / itens.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - valor / 100)

  const linhaAcumulado = linhas
    .map((l, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(l.percentualAcumulado).toFixed(1)}`)
    .join(' ')

  const hover = indiceHover !== null ? linhas[indiceHover] : null

  return (
    <div className="pareto-tendencia-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha serie-pareto-tendencia" /> % acumulado
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha-tracejada" style={{ color: 'var(--cor-texto-suave)' }} /> 80%
          </span>
        </div>
      </div>

      <div className="evolucao-chart-area">
        <svg
          viewBox={`0 0 ${LARGURA} ${ALTURA}`}
          role="img"
          aria-label="Percentual acumulado de despesas por ranking de categoria"
        >
          {MARCACOES.map((v) => (
            <g key={v}>
              <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
              <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                {oculto ? '•••' : `${v}%`}
              </text>
            </g>
          ))}

          <line
            x1={MARGEM.esquerda}
            x2={LARGURA - MARGEM.direita}
            y1={y(CORTE)}
            y2={y(CORTE)}
            className="evolucao-linha-media"
            stroke="var(--cor-texto-suave)"
          />

          {linhas.length > 1 && (
            <path d={linhaAcumulado} className="evolucao-linha" fill="none" stroke="var(--pareto-tendencia-cor)" />
          )}
          {linhas.map((l, i) => (
            <circle
              key={l.id}
              cx={x(i)}
              cy={y(l.percentualAcumulado)}
              r={3}
              className="evolucao-marcador"
              fill="var(--pareto-tendencia-cor)"
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

          {linhas.map((l, i) => (
            <rect
              key={l.id}
              x={MARGEM.esquerda + larguraBanda * i}
              y={MARGEM.topo}
              width={larguraBanda}
              height={ALTURA_PLOT}
              fill="transparent"
              tabIndex={0}
              aria-label={
                oculto
                  ? `${l.nome}: valores ocultos`
                  : `${l.nome}: ${l.percentual.toFixed(1)}% do total, ${l.percentualAcumulado.toFixed(1)}% acumulado`
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
            <strong>{hover.nome}</strong>
            <span>{oculto ? '•••' : `${formatarMoeda(hover.valor)} · ${hover.percentual.toFixed(1)}%`}</span>
            <span>
              <span className="evolucao-legenda-bloco serie-pareto-tendencia" />{' '}
              {oculto ? '•••' : `${hover.percentualAcumulado.toFixed(1)}% acumulado`}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
