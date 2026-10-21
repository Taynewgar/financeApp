import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { corDaSerie } from '../lib/coresSeries'
import { formatarMoeda } from '../lib/formatar'
import { calcularPeriodoGrafico, hojeAnoMes, PERIODOS_GRAFICO } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import { escalaY } from '../lib/escala'
import type { Caixinha, Categoria, SerieMensal, Subcategoria } from '../lib/types'

const LARG = 900
const ALT = 420
const MARG = { topo: 16, base: 32, esq: 64, dir: 70 }
const ALT_PLOT = ALT - MARG.topo - MARG.base
const LIMITE_PADRAO = 5
const COR_MEDIA_PERIODO = '#f59e0b'

const LABEL_ESTRUTURA: Record<string, string> = {
  fixo: 'Fixo',
  variavel: 'Variável',
  sazonal: 'Sazonal',
  investimentos: 'Investimentos',
}

type AbaChave = 'receita' | 'despesaSub' | 'categoriaPai' | 'estrutura' | 'caixinha'
type ItemSerie = { chave: string; nome: string; cor: string; secao?: string }
type LinhaPicker = { tipo: 'cabecalho'; titulo: string } | { tipo: 'item'; item: ItemSerie }
type Modo = 'linha' | 'barra'
type Hover = { x: number; y: number; nome: string; mes: string; valor: number; cor: string }

const ABAS_DEF: { chave: AbaChave; titulo: string }[] = [
  { chave: 'receita', titulo: 'Receita' },
  { chave: 'despesaSub', titulo: 'Despesa (sub)' },
  { chave: 'categoriaPai', titulo: 'Categoria (pai)' },
  { chave: 'estrutura', titulo: 'Estrutura' },
  { chave: 'caixinha', titulo: 'Caixinhas' },
]

/** Item 51/91 do backlog — "comparador dinâmico": qualquer combinação de
 * subcategoria (receita/despesa), categoria pai, estrutura de custo ou
 * aporte/retirada de caixinha, lado a lado no tempo. Picker reorganizado
 * na Rodada 91 (feedback: layout bagunçado, sem categoria pai, sem
 * tooltip) — abas por tipo de série, com busca, corte "mais usadas" nas
 * abas com muitos itens (agrupado por categoria/seção quando expandido),
 * chips removíveis e botão de limpar. As séries já vêm ranqueadas por uso
 * pelo backend (/categorias, /subcategorias e /caixinhas "mais-usadas"
 * com limite alto = lista completa já ordenada — evita reordenar no
 * cliente e mantém 1 única fonte de verdade de "mais usada" no app). */
export function ComparadorSeries() {
  const { oculto } = usePrivacidade()

  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])

  useEffect(() => {
    Promise.all([
      apiFetch<Categoria[]>('/categorias/mais-usadas?limite=500'),
      apiFetch<Subcategoria[]>('/subcategorias/mais-usadas?limite=500'),
      apiFetch<Caixinha[]>('/caixinhas/mais-usadas?limite=500'),
    ])
      .then(([cat, sub, cx]) => {
        setCategorias(cat)
        setSubcategorias(sub)
        setCaixinhas(cx)
      })
      .catch(() => {})
  }, [])

  const categoriasPorId = useMemo(() => new Map(categorias.map((c) => [c.id, c])), [categorias])

  // grupos por aba, nessa ordem fixa — cor por posição na lista inteira
  // (estável independente do que está marcado, filtrado ou expandido)
  const grupos = useMemo(() => {
    let indice = 0
    const proximaCor = () => corDaSerie(indice++)

    const receita: ItemSerie[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'receita')
      .map((s) => ({ chave: `subcategoria:${s.id}`, nome: s.nome, cor: proximaCor() }))

    const despesaSub: ItemSerie[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'despesa')
      .map((s) => ({
        chave: `subcategoria:${s.id}`,
        nome: s.nome,
        cor: proximaCor(),
        secao: categoriasPorId.get(s.categoria_id)?.nome,
      }))

    const catReceita: ItemSerie[] = categorias
      .filter((c) => c.tipo === 'receita')
      .map((c) => ({ chave: `categoria:${c.id}`, nome: c.nome, cor: proximaCor(), secao: 'Receita' }))
    const catDespesa: ItemSerie[] = categorias
      .filter((c) => c.tipo === 'despesa')
      .map((c) => ({ chave: `categoria:${c.id}`, nome: c.nome, cor: proximaCor(), secao: 'Despesa' }))

    const estrutura: ItemSerie[] = (['fixo', 'variavel', 'sazonal', 'investimentos'] as const).map((e) => ({
      chave: `estrutura:${e}`,
      nome: LABEL_ESTRUTURA[e],
      cor: proximaCor(),
    }))

    const caixinhaAporte: ItemSerie[] = caixinhas.map((c) => ({
      chave: `caixinha_aporte:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
      secao: 'Aporte',
    }))
    const caixinhaRetirada: ItemSerie[] = caixinhas.map((c) => ({
      chave: `caixinha_retirada:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
      secao: 'Retirada',
    }))

    const mapa: Record<AbaChave, ItemSerie[]> = {
      receita,
      despesaSub,
      categoriaPai: [...catReceita, ...catDespesa],
      estrutura,
      caixinha: [...caixinhaAporte, ...caixinhaRetirada],
    }
    return mapa
  }, [subcategorias, categorias, categoriasPorId, caixinhas])

  const todasAsSeries = useMemo(() => Object.values(grupos).flat(), [grupos])
  const corPorChave = useMemo(() => new Map(todasAsSeries.map((s) => [s.chave, s.cor])), [todasAsSeries])
  const nomePorChave = useMemo(() => new Map(todasAsSeries.map((s) => [s.chave, s.nome])), [todasAsSeries])

  const [abaAtiva, setAbaAtiva] = useState<AbaChave>('despesaSub')
  const [busca, setBusca] = useState('')
  const [verTodas, setVerTodas] = useState<Partial<Record<AbaChave, boolean>>>({})
  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set())
  const [periodoIndice, setPeriodoIndice] = useState(1)
  const [modo, setModo] = useState<Modo>('linha')
  const [mostrarMediaSeries, setMostrarMediaSeries] = useState(true)
  const [mostrarMediaPeriodo, setMostrarMediaPeriodo] = useState(false)
  const [hover, setHover] = useState<Hover | null>(null)
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

  const { linhas: linhasAba, linkRodape } = useMemo(() => {
    const todos = grupos[abaAtiva] ?? []
    const buscaTexto = busca.trim().toLowerCase()
    const buscaAtiva = buscaTexto.length > 0
    const temCorte = todos.length > LIMITE_PADRAO
    const expandida = !!verTodas[abaAtiva]
    const fazerItem = (s: ItemSerie): LinhaPicker => ({ tipo: 'item', item: s })
    const semLink = { mostrar: false, texto: '', acao: () => {} }

    if (!buscaAtiva && temCorte && !expandida) {
      // já vem ranqueado por uso (backend) — os 5 primeiros são os mais usados
      return {
        linhas: todos.slice(0, LIMITE_PADRAO).map(fazerItem),
        linkRodape: {
          mostrar: true,
          texto: `Mostrando as mais usadas · ver todas (${todos.length})`,
          acao: () => setVerTodas((v) => ({ ...v, [abaAtiva]: true })),
        },
      }
    }

    const filtrados = buscaAtiva ? todos.filter((s) => s.nome.toLowerCase().includes(buscaTexto)) : todos
    const recolher = {
      mostrar: temCorte && expandida && !buscaAtiva,
      texto: 'Recolher pra mais usadas',
      acao: () => setVerTodas((v) => ({ ...v, [abaAtiva]: false })),
    }

    const temSecoes = filtrados.some((s) => s.secao)
    if (temSecoes && !buscaAtiva) {
      const ordemSecoes: string[] = []
      const porSecao = new Map<string, ItemSerie[]>()
      filtrados.forEach((s) => {
        const chaveSecao = s.secao ?? ''
        if (!porSecao.has(chaveSecao)) {
          porSecao.set(chaveSecao, [])
          ordemSecoes.push(chaveSecao)
        }
        porSecao.get(chaveSecao)!.push(s)
      })
      const linhas: LinhaPicker[] = []
      ordemSecoes.forEach((secao) => {
        linhas.push({ tipo: 'cabecalho', titulo: secao })
        porSecao.get(secao)!.forEach((s) => linhas.push(fazerItem(s)))
      })
      return { linhas, linkRodape: recolher.mostrar ? recolher : semLink }
    }

    return { linhas: filtrados.map(fazerItem), linkRodape: recolher.mostrar ? recolher : semLink }
  }, [grupos, abaAtiva, busca, verTodas])

  const periodoAtual = PERIODOS_GRAFICO[periodoIndice]
  const [mesFim] = useState(() => hojeAnoMes())
  const { inicio: mesInicio } = calcularPeriodoGrafico(periodoIndice, mesFim)

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

  // soma bruta por mês primeiro — "média do período" é a média DESSA soma,
  // nunca dividida por nº de séries (bug real descoberto nos mockups da
  // Rodada 91: dividir a média mês-a-mês de novo fazia a média do período
  // CAIR ao marcar mais séries, em vez de acompanhar a soma)
  const somaPorMes = meses.map((_, i) => (series ?? []).reduce((acc, s) => acc + s.pontos[i].valor, 0))
  const mediaPorMes = somaPorMes.map((soma) => ((series?.length ?? 0) > 0 ? soma / series!.length : 0))
  const mediaDoPeriodo = somaPorMes.length ? somaPorMes.reduce((a, b) => a + b, 0) / somaPorMes.length : 0

  const grupoLargura = espacamento * 0.72
  const n = series?.length || 1
  const larguraBarra = Math.max(2, (grupoLargura - (n - 1) * 2) / n)
  const yBase = y(0)

  function rotuloMes(vigenciaMes: string): string {
    const [ano, mes] = vigenciaMes.split('-')
    const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
  }

  const tooltip = useMemo(() => {
    if (!hover) return null
    // o <svg> recorta tudo fora do viewBox (overflow:hidden é o padrão de
    // UA pra <svg> embutido em HTML) — sem esses 2 clamps a caixa nascia
    // com x/y negativo perto das bordas (sobretudo perto do topo, onde
    // ficam os valores mais altos — exatamente onde mais se passa o
    // mouse) e ficava cortada, invisível. Achado real do usuário testando.
    const estouraDireita = hover.x + 190 > LARG - 10
    const rectX = estouraDireita ? hover.x - 190 : hover.x + 10
    const colocarAbaixo = hover.y < ALT / 2
    const rectY = colocarAbaixo ? hover.y + 10 : hover.y - 36
    return {
      cx: hover.x,
      cy: hover.y,
      cor: hover.cor,
      rectX,
      rectY,
      textX: rectX + 10,
      linha1Y: rectY + 18,
      linha2Y: rectY + 32,
      nome: hover.nome,
      mes: hover.mes,
      valor: oculto ? '•••' : formatarMoeda(hover.valor),
    }
  }, [hover, oculto])

  const chipsSelecionadas = Array.from(selecionadas).map((chave) => ({
    chave,
    nome: nomePorChave.get(chave) ?? chave,
    cor: corPorChave.get(chave) ?? 'var(--cor-texto-suave)',
  }))

  return (
    <div className="comparador-series-layout">
      <div className="comparador-abas">
        {ABAS_DEF.map((a) => (
          <button
            key={a.chave}
            type="button"
            className={`comparador-aba-botao ${abaAtiva === a.chave ? 'ativa' : ''}`}
            onClick={() => setAbaAtiva(a.chave)}
          >
            {a.titulo}
          </button>
        ))}
        <input
          className="comparador-busca"
          type="text"
          placeholder="Buscar..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>

      <div className="comparador-faixa">
        {linhasAba.map((l, i) =>
          l.tipo === 'cabecalho' ? (
            <span key={`cab-${i}`} className="comparador-rotulo-secao">
              {l.titulo}
            </span>
          ) : (
            <label key={l.item.chave} className="comparador-item-compacto">
              <input type="checkbox" checked={selecionadas.has(l.item.chave)} onChange={() => alternar(l.item.chave)} />
              <span className="comparador-chip-cor" style={{ background: l.item.cor }} />
              {l.item.nome}
            </label>
          ),
        )}
        {linhasAba.length === 0 && <span className="comparador-faixa-vazia">Nenhuma série encontrada.</span>}
      </div>
      {linkRodape.mostrar && (
        <button type="button" className="comparador-link-mostrar" onClick={linkRodape.acao}>
          {linkRodape.texto}
        </button>
      )}

      <div className="comparador-chips-selecionadas">
        {chipsSelecionadas.map((s) => (
          <span key={s.chave} className="comparador-chip-selecionada" style={{ borderColor: s.cor }}>
            <span className="comparador-chip-cor" style={{ background: s.cor }} />
            {s.nome}
            <button
              type="button"
              className="comparador-chip-remover"
              onClick={() => alternar(s.chave)}
              aria-label={`Remover ${s.nome}`}
            >
              ✕
            </button>
          </span>
        ))}
        {selecionadas.size === 0 && (
          <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>Nenhuma série selecionada ainda.</span>
        )}
        <button
          type="button"
          className="botao-chip"
          style={{ marginLeft: 'auto', borderColor: 'var(--cor-perigo)', color: 'var(--cor-perigo)' }}
          onClick={() => setSelecionadas(new Set())}
        >
          ✕ Limpar seleções
        </button>
      </div>

      <div className="comparador-controles">
        <button type="button" className="botao-chip" onClick={() => setPeriodoIndice((i) => (i + 1) % PERIODOS_GRAFICO.length)}>
          📅 {periodoAtual.label} ▾
        </button>
        <button type="button" className={`botao-chip ${modo === 'linha' ? 'ativo' : ''}`} onClick={() => setModo('linha')}>
          ╱ Linhas
        </button>
        <button type="button" className={`botao-chip ${modo === 'barra' ? 'ativo' : ''}`} onClick={() => setModo('barra')}>
          ▥ Barras
        </button>
        <button
          type="button"
          className={`botao-chip ${mostrarMediaSeries ? 'ativo' : ''}`}
          onClick={() => setMostrarMediaSeries((v) => !v)}
        >
          ⟂ Média entre as séries
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
          {(series ?? []).map((s) => (
            <span key={s.chave} className="comparador-legenda-item">
              <span className="comparador-chip-cor" style={{ background: corPorChave.get(s.chave) }} />
              {nomePorChave.get(s.chave) ?? s.nome}
            </span>
          ))}
          {selecionadas.size === 0 && (
            <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>
              Nenhuma série selecionada — marque alguma acima.
            </span>
          )}
          {mostrarMediaSeries && series && series.length >= 2 && (
            <span className="comparador-legenda-item">
              <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: '2px dashed var(--cor-texto)' }} />
              Média entre as séries
            </span>
          )}
          {mostrarMediaPeriodo && series && series.length >= 1 && (
            <span className="comparador-legenda-item">
              <span style={{ display: 'inline-block', width: 14, height: 2, borderTop: `2px dashed ${COR_MEDIA_PERIODO}` }} />
              Média do período: {oculto ? '•••' : formatarMoeda(mediaDoPeriodo)}
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
                    <g key={i}>
                      <circle cx={x(i)} cy={y(p.valor)} r={3.5} fill={corPorChave.get(s.chave)} />
                      {/* círculo invisível maior só pra facilitar o hover — o
                       * ponto visível (r=3.5) é pequeno demais de acertar */}
                      <circle
                        cx={x(i)}
                        cy={y(p.valor)}
                        r={10}
                        fill="transparent"
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={() =>
                          setHover({
                            x: x(i),
                            y: y(p.valor),
                            nome: nomePorChave.get(s.chave) ?? s.nome,
                            mes: rotuloMes(p.vigencia_mes),
                            valor: p.valor,
                            cor: corPorChave.get(s.chave) ?? 'var(--cor-texto)',
                          })
                        }
                        onMouseLeave={() => setHover(null)}
                      />
                    </g>
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
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() =>
                        setHover({
                          x: xBarra + larguraBarra / 2,
                          y: yTopo,
                          nome: nomePorChave.get(s.chave) ?? s.nome,
                          mes: rotuloMes(meses[i]),
                          valor: v,
                          cor: corPorChave.get(s.chave) ?? 'var(--cor-texto)',
                        })
                      }
                      onMouseLeave={() => setHover(null)}
                    />
                  )
                }),
              )}

            {mostrarMediaSeries && series.length >= 2 && (
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

            {mostrarMediaPeriodo && series.length >= 1 && (
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

            {tooltip && (
              <g>
                <circle cx={tooltip.cx} cy={tooltip.cy} r={6} fill="none" stroke={tooltip.cor} strokeWidth={2} />
                <rect x={tooltip.rectX} y={tooltip.rectY} width={170} height={34} rx={6} fill="var(--cor-superficie)" stroke={tooltip.cor} strokeWidth={1.5} />
                <text x={tooltip.textX} y={tooltip.linha1Y} className="comparador-tooltip-titulo" fill={tooltip.cor}>
                  {tooltip.nome}
                </text>
                <text x={tooltip.textX} y={tooltip.linha2Y} className="comparador-tooltip-texto">
                  {tooltip.mes} · {tooltip.valor}
                </text>
              </g>
            )}
          </svg>
        )}
      </div>
    </div>
  )
}
