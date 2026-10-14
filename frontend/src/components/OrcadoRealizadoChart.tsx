import { useState } from 'react'
import './evolucaoChart.css'
import { escalaY } from '../lib/escala'
import { formatarMoeda } from '../lib/formatar'
import { media, type BaseMedia } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import type { PontoTendenciaOrcamento } from '../lib/types'

const LARGURA = 600
const ALTURA = 220
const MARGEM = { topo: 12, base: 28, esquerda: 52, direita: 12 }
const ALTURA_PLOT = ALTURA - MARGEM.topo - MARGEM.base

const MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function rotuloMes(vigenciaMes: string): string {
  const [ano, mes] = vigenciaMes.split('-')
  return `${MESES_ABREV[Number(mes) - 1]}/${ano.slice(2)}`
}

/** Orçado × Realizado em vários meses — resumo que complementa Estrutura
 * de Custo (leitura de 1 mês só). Escopo igual ao KPI "Orçado no mês":
 * só o pool de despesas (fixos+variáveis+sazonalidades), sem investimentos
 * (ver backend `_estrutura_custo_do_mes`/evolucao). */
export function OrcadoRealizadoChart({
  meses,
  baseMedia = 'ate_mes',
}: {
  meses: PontoTendenciaOrcamento[]
  baseMedia?: BaseMedia
}) {
  const { oculto } = usePrivacidade()
  const [indiceHover, setIndiceHover] = useState<number | null>(null)
  const [mostrarTabela, setMostrarTabela] = useState(false)

  if (meses.length === 0) {
    return <p style={{ color: 'var(--cor-texto-suave)' }}>Sem dados no período.</p>
  }

  const valores = meses.flatMap((m) => [m.orcado, m.realizado, 0])
  const { min, max, marcacoes } = escalaY(valores)

  const larguraBanda = (LARGURA - MARGEM.esquerda - MARGEM.direita) / meses.length
  const x = (i: number) => MARGEM.esquerda + larguraBanda * (i + 0.5)
  const y = (valor: number) => MARGEM.topo + ALTURA_PLOT * (1 - (valor - min) / (max - min || 1))
  const yBase = y(0)

  const grupoLargura = larguraBanda * 0.6
  const barraLargura = (grupoLargura - 2) / 2
  const xOrcado = (i: number) => x(i) - grupoLargura / 2
  const xRealizado = (i: number) => xOrcado(i) + barraLargura + 2
  const retanguloBarra = (valor: number) => ({
    y: Math.min(yBase, y(valor)),
    altura: Math.abs(yBase - y(valor)),
  })

  const mediaOrcado = media(meses.map((m) => m.orcado), baseMedia)
  const mediaRealizado = media(meses.map((m) => m.realizado), baseMedia)

  const hover = indiceHover !== null ? meses[indiceHover] : null

  return (
    <div className="evolucao-chart">
      <div className="evolucao-chart-cabecalho">
        <div className="evolucao-legenda">
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-bloco serie-receitas" /> Orçado
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-bloco serie-despesas" /> Realizado
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha-tracejada serie-receitas" /> Média orçado (
            {formatarMoeda(mediaOrcado, oculto)})
          </span>
          <span className="evolucao-legenda-item">
            <span className="evolucao-legenda-linha-tracejada serie-despesas" /> Média realizado (
            {formatarMoeda(mediaRealizado, oculto)})
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
              <th>Orçado</th>
              <th>Realizado</th>
              <th>% executado</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.vigencia_mes}>
                <td>{rotuloMes(m.vigencia_mes)}</td>
                <td>{formatarMoeda(m.orcado, oculto)}</td>
                <td>{formatarMoeda(m.realizado, oculto)}</td>
                <td>{m.percentual_executado === null ? '—' : `${m.percentual_executado.toFixed(1)}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="evolucao-chart-area">
          <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} role="img" aria-label="Orçado x Realizado por mês">
            {marcacoes.map((v) => (
              <g key={v}>
                <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="evolucao-grade" />
                <text x={MARGEM.esquerda - 6} y={y(v)} className="evolucao-eixo-texto" textAnchor="end" dominantBaseline="middle">
                  {oculto ? '•••' : formatarMoeda(v).replace('R$', '').trim()}
                </text>
              </g>
            ))}

            <line
              x1={MARGEM.esquerda}
              x2={LARGURA - MARGEM.direita}
              y1={y(mediaOrcado)}
              y2={y(mediaOrcado)}
              className="evolucao-linha-media"
              stroke="var(--serie-receitas)"
            />
            <line
              x1={MARGEM.esquerda}
              x2={LARGURA - MARGEM.direita}
              y1={y(mediaRealizado)}
              y2={y(mediaRealizado)}
              className="evolucao-linha-media"
              stroke="var(--serie-despesas)"
            />

            {meses.map((m, i) => {
              const orcado = retanguloBarra(m.orcado)
              const realizado = retanguloBarra(m.realizado)
              return (
                <g key={m.vigencia_mes}>
                  <rect x={xOrcado(i)} y={orcado.y} width={barraLargura} height={orcado.altura} rx={3} fill="var(--serie-receitas)" />
                  <rect
                    x={xRealizado(i)}
                    y={realizado.y}
                    width={barraLargura}
                    height={realizado.altura}
                    rx={3}
                    fill="var(--serie-despesas)"
                  />
                  <text x={x(i)} y={ALTURA - 8} className="evolucao-eixo-texto" textAnchor="middle">
                    {rotuloMes(m.vigencia_mes)}
                  </text>
                </g>
              )
            })}

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
                    ? `${rotuloMes(meses[i].vigencia_mes)}: valores ocultos`
                    : `${rotuloMes(meses[i].vigencia_mes)}: orçado ${formatarMoeda(meses[i].orcado)}, realizado ${formatarMoeda(meses[i].realizado)}`
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
                <span className="evolucao-legenda-bloco serie-receitas" /> {formatarMoeda(hover.orcado, oculto)}
              </span>
              <span>
                <span className="evolucao-legenda-bloco serie-despesas" /> {formatarMoeda(hover.realizado, oculto)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
