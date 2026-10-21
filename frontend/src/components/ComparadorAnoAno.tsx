import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { corDaSerie } from '../lib/coresSeries'
import { formatarMoeda } from '../lib/formatar'
import { hojeAnoMes } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, Categoria, SerieMensal, Subcategoria } from '../lib/types'

const LARG = 900
const ALT = 420
const MARG = { topo: 16, base: 32, esq: 64, dir: 70 }
const ALT_PLOT = ALT - MARG.topo - MARG.base
const QTD_ANOS_OPCOES = [2, 3, 5]
const COR_MEDIA_PERIODO = '#f59e0b'

const LABEL_ESTRUTURA: Record<string, string> = {
  fixo: 'Fixo',
  variavel: 'Variável',
  sazonal: 'Sazonal',
  investimentos: 'Investimentos',
}

type Opcao = { chave: string; nome: string }
type Modo = 'linha' | 'barra'

/** Item 51 do backlog — comparador "ano a ano": escolhe UMA série
 * (subcategoria, estrutura de custo ou caixinha) e sobrepõe os últimos
 * 3 anos, mês a mês, pra ver sazonalidade/evolução ano contra ano. */
export function ComparadorAnoAno() {
  const { oculto } = usePrivacidade()

  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])

  useEffect(() => {
    Promise.all([
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Caixinha[]>('/caixinhas'),
    ])
      .then(([cat, sub, cx]) => {
        setCategorias(cat.filter((c) => c.ativo))
        setSubcategorias(sub.filter((s) => s.ativo))
        setCaixinhas(cx.filter((c) => c.ativo))
      })
      .catch(() => {})
  }, [])

  const categoriasPorId = useMemo(() => new Map(categorias.map((c) => [c.id, c])), [categorias])

  const opcoes: Opcao[] = useMemo(() => {
    const subOpcoes = subcategorias.map((s) => ({
      chave: `subcategoria:${s.id}`,
      nome: `${categoriasPorId.get(s.categoria_id)?.tipo === 'receita' ? 'Receita' : 'Despesa'} · ${s.nome}`,
    }))
    const estruturaOpcoes = (['fixo', 'variavel', 'sazonal', 'investimentos'] as const).map((e) => ({
      chave: `estrutura:${e}`,
      nome: `Estrutura · ${LABEL_ESTRUTURA[e]}`,
    }))
    const caixinhaOpcoes = caixinhas.map((c) => ({ chave: `caixinha_aporte:${c.id}`, nome: `Caixinha · ${c.nome}` }))
    return [...subOpcoes, ...estruturaOpcoes, ...caixinhaOpcoes]
  }, [subcategorias, categoriasPorId, caixinhas])

  const [chaveSelecionada, setChaveSelecionada] = useState<string | null>(null)
  const [modo, setModo] = useState<Modo>('linha')
  const [mostrarMedia, setMostrarMedia] = useState(true)
  const [mostrarMediaPeriodo, setMostrarMediaPeriodo] = useState(false)
  const [anosIndice, setAnosIndice] = useState(1) // índice em QTD_ANOS_OPCOES — 3 anos por padrão
  const [porAno, setPorAno] = useState<Map<string, SerieMensal> | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (opcoes.length > 0 && chaveSelecionada === null) setChaveSelecionada(opcoes[0].chave)
  }, [opcoes, chaveSelecionada])

  const qtdAnos = QTD_ANOS_OPCOES[anosIndice]
  const anoAtual = Number(hojeAnoMes().slice(0, 4))
  const anos = useMemo(
    () => Array.from({ length: qtdAnos }, (_, i) => anoAtual - (qtdAnos - 1) + i),
    [anoAtual, qtdAnos],
  )

  useEffect(() => {
    if (!chaveSelecionada) return
    const inicio = `${anos[0]}-01-01`
    const fim = `${anos[anos.length - 1]}-12-01`
    apiFetch<SerieMensal[]>(`/dashboard/series-mensais?${new URLSearchParams({ series: chaveSelecionada, inicio, fim }).toString()}`)
      .then((r) => {
        const serieUnica = r[0]
        const mapa = new Map<string, SerieMensal>()
        anos.forEach((ano) => {
          const pontos = serieUnica.pontos.filter((p) => p.vigencia_mes.startsWith(String(ano)))
          mapa.set(String(ano), { chave: String(ano), nome: String(ano), pontos })
        })
        setPorAno(mapa)
        setErro(null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o comparador ano a ano'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveSelecionada, qtdAnos])

  const mesesDoAno = Array.from({ length: 12 }, (_, i) => i + 1)
  const todosValores = porAno ? Array.from(porAno.values()).flatMap((s) => s.pontos.map((p) => p.valor)) : []
  const { min, max, marcacoes } = escalaY(todosValores)

  const espacamento = (LARG - MARG.esq - MARG.dir) / 11
  const x = (mesIndice: number) => MARG.esq + espacamento * mesIndice
  const y = (v: number) => MARG.topo + ALT_PLOT * (1 - (v - min) / (max - min || 1))
  const yBase = y(0)

  const mediaPorMes = mesesDoAno.map((_, i) => {
    if (!porAno) return 0
    const valores = Array.from(porAno.values())
      .map((s) => s.pontos[i]?.valor)
      .filter((v): v is number => v !== undefined)
    return valores.length > 0 ? valores.reduce((a, b) => a + b, 0) / valores.length : 0
  })

  // soma bruta por mês primeiro — "média do período" é a média DESSA soma,
  // nunca dividida por nº de anos de novo (mesmo bug achado nos mockups do
  // Comparador de Séries: dividir a média mês-a-mês mais uma vez fazia a
  // média do período CAIR ao comparar mais anos, em vez de acompanhar a soma)
  const somaPorMes = mesesDoAno.map((_, i) => {
    if (!porAno) return 0
    return Array.from(porAno.values()).reduce((acc, s) => acc + (s.pontos[i]?.valor ?? 0), 0)
  })
  const mediaDoPeriodo = somaPorMes.length ? somaPorMes.reduce((a, b) => a + b, 0) / somaPorMes.length : 0

  const nomeSelecionado = opcoes.find((o) => o.chave === chaveSelecionada)?.nome ?? ''
  const nomesMes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  const grupoLargura = espacamento * 0.72
  const listaAnos = porAno ? Array.from(porAno.entries()) : []
  const n = listaAnos.length || 1
  const larguraBarra = Math.max(2, (grupoLargura - (n - 1) * 2) / n)

  return (
    <div className="comparador-layout">
      <div className="comparador-picker" style={{ width: 240 }}>
        <div className="comparador-grupo-titulo">Série (um item por vez)</div>
        {opcoes.map((o) => (
          <label key={o.chave} className="comparador-item-serie">
            <input
              type="radio"
              name="serie-ano-ano"
              checked={chaveSelecionada === o.chave}
              onChange={() => setChaveSelecionada(o.chave)}
            />
            {o.nome}
          </label>
        ))}
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <div className="comparador-controles">
          <button
            type="button"
            className="botao-chip"
            onClick={() => setAnosIndice((i) => (i + 1) % QTD_ANOS_OPCOES.length)}
          >
            📅 {anos[0]}–{anos[anos.length - 1]} ({qtdAnos} anos) ▾
          </button>
          <button type="button" className={`botao-chip ${modo === 'linha' ? 'ativo' : ''}`} onClick={() => setModo('linha')}>
            ╱ Linhas
          </button>
          <button type="button" className={`botao-chip ${modo === 'barra' ? 'ativo' : ''}`} onClick={() => setModo('barra')}>
            ▥ Barras
          </button>
          <button
            type="button"
            className={`botao-chip ${mostrarMedia ? 'ativo' : ''}`}
            onClick={() => setMostrarMedia((v) => !v)}
          >
            ⟂ Média entre os anos
          </button>
          <button
            type="button"
            className={`botao-chip ${mostrarMediaPeriodo ? 'ativo-laranja' : ''}`}
            onClick={() => setMostrarMediaPeriodo((v) => !v)}
          >
            — Média do período
          </button>
        </div>

        {erro && <p className="mensagem-erro">{erro}</p>}

        <div className="comparador-chart-card">
          <div className="comparador-legenda">
            {nomeSelecionado && (
              <span className="comparador-legenda-item" style={{ color: 'var(--cor-texto)', fontWeight: 600 }}>
                Série: {nomeSelecionado}
              </span>
            )}
            {listaAnos.map(([ano], i) => (
              <span key={ano} className="comparador-legenda-item">
                <span className="comparador-chip-cor" style={{ background: corDaSerie(i) }} />
                {ano}
              </span>
            ))}
            {mostrarMedia && listaAnos.length >= 2 && (
              <span className="comparador-legenda-item">
                <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: '2px dashed var(--cor-texto)' }} />
                Média entre os anos
              </span>
            )}
            {mostrarMediaPeriodo && listaAnos.length >= 1 && (
              <span className="comparador-legenda-item">
                <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: `2px dashed ${COR_MEDIA_PERIODO}` }} />
                Média do período: {oculto ? '•••' : formatarMoeda(mediaDoPeriodo)}
              </span>
            )}
          </div>

          {porAno && (
            <svg viewBox={`0 0 ${LARG} ${ALT}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Comparador ano a ano">
              {marcacoes.map((v) => (
                <g key={v}>
                  <line x1={MARG.esq} x2={LARG - MARG.dir} y1={y(v)} y2={y(v)} className="comparador-grade" />
                  <text x={MARG.esq - 8} y={y(v)} className="comparador-eixo-texto" textAnchor="end" dominantBaseline="middle">
                    {oculto ? '•••' : formatarMoeda(v).replace('R$', '').trim()}
                  </text>
                </g>
              ))}
              {mesesDoAno.map((_, i) => (
                <text key={i} x={x(i)} y={ALT - 10} className="comparador-eixo-texto" textAnchor="middle">
                  {nomesMes[i]}
                </text>
              ))}

              {modo === 'linha' &&
                listaAnos.map(([ano, serie], i) => (
                  <g key={ano}>
                    <path
                      d={serie.pontos.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${x(idx).toFixed(1)} ${y(p.valor).toFixed(1)}`).join(' ')}
                      fill="none"
                      stroke={corDaSerie(i)}
                      strokeWidth={2.5}
                    />
                    {serie.pontos.map((p, idx) => (
                      <circle key={idx} cx={x(idx)} cy={y(p.valor)} r={3.5} fill={corDaSerie(i)} />
                    ))}
                  </g>
                ))}

              {modo === 'barra' &&
                mesesDoAno.map((_, i) =>
                  listaAnos.map(([ano, serie], k) => {
                    const v = serie.pontos[i]?.valor ?? 0
                    const xBarra = x(i) - grupoLargura / 2 + k * (larguraBarra + 2)
                    const yTopo = Math.min(yBase, y(v))
                    return (
                      <rect
                        key={ano}
                        x={xBarra}
                        y={yTopo}
                        width={larguraBarra}
                        height={Math.abs(yBase - y(v))}
                        rx={2}
                        fill={corDaSerie(k)}
                      />
                    )
                  }),
                )}

              {mostrarMedia && listaAnos.length >= 2 && (
                <>
                  <path
                    d={mediaPorMes.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')}
                    fill="none"
                    stroke="var(--cor-texto)"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                  />
                  {mediaPorMes.map((v, i) => (
                    <circle key={i} cx={x(i)} cy={y(v)} r={3} fill="var(--cor-texto)" />
                  ))}
                </>
              )}

              {mostrarMediaPeriodo && listaAnos.length >= 1 && (
                <line
                  x1={MARG.esq}
                  x2={LARG - MARG.dir}
                  y1={y(mediaDoPeriodo)}
                  y2={y(mediaDoPeriodo)}
                  stroke={COR_MEDIA_PERIODO}
                  strokeWidth={2}
                  strokeDasharray="3 5"
                />
              )}
            </svg>
          )}
        </div>
      </div>
    </div>
  )
}
