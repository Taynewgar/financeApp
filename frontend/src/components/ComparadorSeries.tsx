import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { corDaSerie } from '../lib/coresSeries'
import { formatarMoeda } from '../lib/formatar'
import { hojeAnoMes, mesesAntes } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, Categoria, SerieMensal, Subcategoria } from '../lib/types'

const LARG = 900
const ALT = 420
const MARG = { topo: 16, base: 32, esq: 64, dir: 16 }
const ALT_PLOT = ALT - MARG.topo - MARG.base

const LABEL_ESTRUTURA: Record<string, string> = {
  fixo: 'Fixo',
  variavel: 'Variável',
  sazonal: 'Sazonal',
  investimentos: 'Investimentos',
}

type SerieDisponivel = { chave: string; nome: string; cor: string }
type Modo = 'linha' | 'barra'

/** Item 51 do backlog — "comparador dinâmico": qualquer combinação de
 * subcategoria (receita/despesa), estrutura de custo ou aporte/retirada
 * de caixinha, lado a lado no tempo. Ideia do usuário: liberdade total
 * de escolha, tipo escolher colunas numa planilha pra montar a
 * comparação que quiser. */
export function ComparadorSeries() {
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

  // grupos fixos, nessa ordem — cor por posição na lista inteira (estável
  // independente do que está marcado ou não)
  const grupos = useMemo(() => {
    let indice = 0
    const proximaCor = () => corDaSerie(indice++)

    const subReceita: SerieDisponivel[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'receita')
      .map((s) => ({ chave: `subcategoria:${s.id}`, nome: s.nome, cor: proximaCor() }))

    const subDespesa: SerieDisponivel[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'despesa')
      .map((s) => ({ chave: `subcategoria:${s.id}`, nome: s.nome, cor: proximaCor() }))

    const estrutura: SerieDisponivel[] = (['fixo', 'variavel', 'sazonal', 'investimentos'] as const).map((e) => ({
      chave: `estrutura:${e}`,
      nome: LABEL_ESTRUTURA[e],
      cor: proximaCor(),
    }))

    const caixinhaAporte: SerieDisponivel[] = caixinhas.map((c) => ({
      chave: `caixinha_aporte:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
    }))

    const caixinhaRetirada: SerieDisponivel[] = caixinhas.map((c) => ({
      chave: `caixinha_retirada:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
    }))

    return [
      { titulo: 'Receita · subcategoria', itens: subReceita },
      { titulo: 'Despesa · subcategoria', itens: subDespesa },
      { titulo: 'Despesa · estrutura de custo', itens: estrutura },
      { titulo: 'Caixinhas · aporte', itens: caixinhaAporte },
      { titulo: 'Caixinhas · retirada', itens: caixinhaRetirada },
    ].filter((g) => g.itens.length > 0)
  }, [subcategorias, categoriasPorId, caixinhas])

  const corPorChave = useMemo(() => {
    const mapa = new Map<string, string>()
    grupos.forEach((g) => g.itens.forEach((i) => mapa.set(i.chave, i.cor)))
    return mapa
  }, [grupos])

  const nomePorChave = useMemo(() => {
    const mapa = new Map<string, string>()
    grupos.forEach((g) => g.itens.forEach((i) => mapa.set(i.chave, i.nome)))
    return mapa
  }, [grupos])

  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set())
  const [mesInicio] = useState(() => mesesAntes(hojeAnoMes(), 11))
  const [mesFim] = useState(() => hojeAnoMes())
  const [modo, setModo] = useState<Modo>('linha')
  const [mostrarMedia, setMostrarMedia] = useState(true)
  const [series, setSeries] = useState<SerieMensal[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  function alternar(chave: string) {
    setSelecionadas((atual) => {
      const novo = new Set(atual)
      if (novo.has(chave)) novo.delete(chave)
      else novo.add(chave)
      return novo
    })
  }

  useEffect(() => {
    if (selecionadas.size === 0) {
      setSeries([])
      return
    }
    const params = new URLSearchParams({ inicio: `${mesInicio}-01`, fim: `${mesFim}-01` })
    selecionadas.forEach((chave) => params.append('series', chave))
    apiFetch<SerieMensal[]>(`/dashboard/series-mensais?${params.toString()}`)
      .then((r) => {
        setSeries(r)
        setErro(null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o comparador'))
  }, [selecionadas, mesInicio, mesFim])

  const meses = series && series.length > 0 ? series[0].pontos.map((p) => p.vigencia_mes) : []
  const todosValores = (series ?? []).flatMap((s) => s.pontos.map((p) => p.valor))
  const { min, max, marcacoes } = escalaY(todosValores)

  const espacamento = meses.length > 1 ? (LARG - MARG.esq - MARG.dir) / (meses.length - 1) : 0
  const x = (i: number) => (meses.length > 1 ? MARG.esq + espacamento * i : MARG.esq)
  const y = (v: number) => MARG.topo + ALT_PLOT * (1 - (v - min) / (max - min || 1))

  const mediaPorMes = meses.map((_, i) => {
    if (!series || series.length === 0) return 0
    const soma = series.reduce((acc, s) => acc + s.pontos[i].valor, 0)
    return soma / series.length
  })

  const grupoLargura = espacamento * 0.72
  const n = series?.length || 1
  const larguraBarra = Math.max(2, (grupoLargura - (n - 1) * 2) / n)
  const yBase = y(0)

  function rotuloMes(vigenciaMes: string): string {
    const [ano, mes] = vigenciaMes.split('-')
    const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
  }

  return (
    <div className="comparador-layout">
      <div className="comparador-picker">
        {grupos.map((g) => (
          <div key={g.titulo}>
            <div className="comparador-grupo-titulo">{g.titulo}</div>
            {g.itens.map((s) => (
              <label key={s.chave} className="comparador-item-serie">
                <input type="checkbox" checked={selecionadas.has(s.chave)} onChange={() => alternar(s.chave)} />
                <span className="comparador-chip-cor" style={{ background: s.cor }} />
                {s.nome}
              </label>
            ))}
          </div>
        ))}
        {grupos.length === 0 && <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13 }}>Carregando séries…</p>}
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <div className="comparador-controles">
          <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>
            Período: {mesInicio} — {mesFim}
          </span>
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
            ⟂ Média das selecionadas
          </button>
        </div>

        {erro && <p className="mensagem-erro">{erro}</p>}

        <div className="comparador-chart-card">
          <div className="comparador-legenda">
            {(series ?? []).map((s) => (
              <span key={s.chave} className="comparador-legenda-item">
                <span className="comparador-chip-cor" style={{ background: corPorChave.get(s.chave) }} />
                {nomePorChave.get(s.chave) ?? s.nome}
              </span>
            ))}
            {selecionadas.size === 0 && (
              <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>
                Nenhuma série selecionada — marque alguma ao lado.
              </span>
            )}
            {mostrarMedia && series && series.length >= 2 && (
              <span className="comparador-legenda-item">
                <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: '2px dashed var(--cor-texto)' }} />
                Média ({series.length} séries)
              </span>
            )}
          </div>

          {series && series.length > 0 && (
            <svg viewBox={`0 0 ${LARG} ${ALT}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Comparador de séries no tempo">
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

              {modo === 'linha' &&
                series.map((s) => (
                  <g key={s.chave}>
                    <path
                      d={s.pontos.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(p.valor).toFixed(1)}`).join(' ')}
                      fill="none"
                      stroke={corPorChave.get(s.chave)}
                      strokeWidth={2.5}
                    />
                    {s.pontos.map((p, i) => (
                      <circle key={i} cx={x(i)} cy={y(p.valor)} r={3.5} fill={corPorChave.get(s.chave)} />
                    ))}
                  </g>
                ))}

              {modo === 'barra' &&
                meses.map((_, i) =>
                  series.map((s, k) => {
                    const v = s.pontos[i].valor
                    const xBarra = x(i) - grupoLargura / 2 + k * (larguraBarra + 2)
                    const yTopo = Math.min(yBase, y(v))
                    return (
                      <rect
                        key={s.chave}
                        x={xBarra}
                        y={yTopo}
                        width={larguraBarra}
                        height={Math.abs(yBase - y(v))}
                        rx={2}
                        fill={corPorChave.get(s.chave)}
                      />
                    )
                  }),
                )}

              {mostrarMedia && series.length >= 2 && (
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
            </svg>
          )}
        </div>
      </div>
    </div>
  )
}
