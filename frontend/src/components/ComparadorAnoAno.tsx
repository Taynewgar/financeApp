import { useEffect, useMemo, useState } from 'react'
import './graficosComparativos.css'
import { ApiError, apiFetch } from '../lib/api'
import { corDaSerie } from '../lib/coresSeries'
import { formatarMoeda } from '../lib/formatar'
import { hojeAnoMes } from '../lib/periodo'
import { montarLinhasPicker, type ItemPicker } from '../lib/pickerSeries'
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

type AbaChave = 'receita' | 'despesaSub' | 'categoriaPai' | 'estrutura' | 'caixinha'
const ABAS_DEF: { chave: AbaChave; titulo: string }[] = [
  { chave: 'receita', titulo: 'Receita' },
  { chave: 'despesaSub', titulo: 'Despesa (sub)' },
  { chave: 'categoriaPai', titulo: 'Categoria (pai)' },
  { chave: 'estrutura', titulo: 'Estrutura' },
  { chave: 'caixinha', titulo: 'Caixinhas' },
]

const NOMES_MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

/** Item 51/91 do backlog — comparador "ano a ano": escolhe UMA série
 * (subcategoria, categoria pai, estrutura de custo ou caixinha) e
 * sobrepõe N anos, mês a mês, pra ver sazonalidade/evolução. Rodada 98:
 * picker reaproveita a mesma estrutura em abas do Comparador de Séries
 * (antes era uma lista de rádio gigante, desproporcional ao gráfico) e
 * ganhou o mesmo tooltip por coluna do mês inteiro. */
export function ComparadorAnoAno() {
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

  const grupos = useMemo(() => {
    let indice = 0
    const proximaCor = () => corDaSerie(indice++)

    const receita: ItemPicker[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'receita')
      .map((s) => ({ chave: `subcategoria:${s.id}`, nome: s.nome, cor: proximaCor() }))

    const despesaSub: ItemPicker[] = subcategorias
      .filter((s) => categoriasPorId.get(s.categoria_id)?.tipo === 'despesa')
      .map((s) => ({
        chave: `subcategoria:${s.id}`,
        nome: s.nome,
        cor: proximaCor(),
        secao: categoriasPorId.get(s.categoria_id)?.nome,
      }))

    const catReceita: ItemPicker[] = categorias
      .filter((c) => c.tipo === 'receita')
      .map((c) => ({ chave: `categoria:${c.id}`, nome: c.nome, cor: proximaCor(), secao: 'Receita' }))
    const catDespesa: ItemPicker[] = categorias
      .filter((c) => c.tipo === 'despesa')
      .map((c) => ({ chave: `categoria:${c.id}`, nome: c.nome, cor: proximaCor(), secao: 'Despesa' }))

    const estrutura: ItemPicker[] = (['fixo', 'variavel', 'sazonal', 'investimentos'] as const).map((e) => ({
      chave: `estrutura:${e}`,
      nome: LABEL_ESTRUTURA[e],
      cor: proximaCor(),
    }))

    const caixinhaAporte: ItemPicker[] = caixinhas.map((c) => ({
      chave: `caixinha_aporte:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
      secao: 'Aporte',
    }))
    const caixinhaRetirada: ItemPicker[] = caixinhas.map((c) => ({
      chave: `caixinha_retirada:${c.id}`,
      nome: c.nome,
      cor: proximaCor(),
      secao: 'Retirada',
    }))

    const mapa: Record<AbaChave, ItemPicker[]> = {
      receita,
      despesaSub,
      categoriaPai: [...catReceita, ...catDespesa],
      estrutura,
      caixinha: [...caixinhaAporte, ...caixinhaRetirada],
    }
    return mapa
  }, [subcategorias, categorias, categoriasPorId, caixinhas])

  const todasAsSeries = useMemo(() => Object.values(grupos).flat(), [grupos])
  const nomePorChave = useMemo(() => new Map(todasAsSeries.map((s) => [s.chave, s.nome])), [todasAsSeries])

  const [abaAtiva, setAbaAtiva] = useState<AbaChave>('despesaSub')
  const [busca, setBusca] = useState('')
  const [verTodas, setVerTodas] = useState<Partial<Record<AbaChave, boolean>>>({})
  const [chaveSelecionada, setChaveSelecionada] = useState<string | null>(null)
  const [modo, setModo] = useState<'linha' | 'barra'>('linha')
  const [mostrarMedia, setMostrarMedia] = useState(true)
  const [mostrarMediaPeriodo, setMostrarMediaPeriodo] = useState(false)
  const [anosIndice, setAnosIndice] = useState(1) // índice em QTD_ANOS_OPCOES — 3 anos por padrão
  const [hoverIndice, setHoverIndice] = useState<number | null>(null)
  const [porAno, setPorAno] = useState<Map<string, SerieMensal> | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (chaveSelecionada !== null) return
    const candidatos = grupos.despesaSub.length > 0 ? grupos.despesaSub : todasAsSeries
    if (candidatos.length > 0) setChaveSelecionada(candidatos[0].chave)
  }, [grupos, todasAsSeries, chaveSelecionada])

  const expandida = !!verTodas[abaAtiva]
  const { linhas: linhasAba, temCorte } = useMemo(
    () => montarLinhasPicker(grupos[abaAtiva] ?? [], busca, expandida),
    [grupos, abaAtiva, busca, expandida],
  )
  const buscaAtiva = busca.trim().length > 0
  const linkRodape = !buscaAtiva && temCorte && !expandida
    ? {
        mostrar: true,
        texto: `Mostrando as mais usadas · ver todas (${(grupos[abaAtiva] ?? []).length})`,
        acao: () => setVerTodas((v) => ({ ...v, [abaAtiva]: true })),
      }
    : temCorte && expandida && !buscaAtiva
      ? { mostrar: true, texto: 'Recolher pra mais usadas', acao: () => setVerTodas((v) => ({ ...v, [abaAtiva]: false })) }
      : { mostrar: false, texto: '', acao: () => {} }

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

  const nomeSelecionado = nomePorChave.get(chaveSelecionada ?? '') ?? ''
  const grupoLargura = espacamento * 0.72
  const listaAnos = porAno ? Array.from(porAno.entries()) : []
  const n = listaAnos.length || 1
  const larguraBarra = Math.max(2, (grupoLargura - (n - 1) * 2) / n)

  // Rodada 98: mesmo tooltip por coluna do mês do Comparador de Séries —
  // hover em qualquer lugar da coluna, lista todos os anos + a média de
  // uma vez, caixa ancorada perto do topo (nunca sai do viewBox do <svg>).
  const linhasTooltip =
    hoverIndice !== null && porAno
      ? [
          ...listaAnos.map(([ano], i) => ({
            nome: String(ano),
            cor: corDaSerie(i),
            valor: oculto ? '•••' : formatarMoeda(listaAnos[i][1].pontos[hoverIndice]?.valor ?? 0),
          })),
          ...(mostrarMedia && listaAnos.length >= 2
            ? [{ nome: 'Média entre os anos', cor: 'var(--cor-texto)', valor: oculto ? '•••' : formatarMoeda(mediaPorMes[hoverIndice]) }]
            : []),
        ]
      : null

  const tooltip =
    hoverIndice !== null && linhasTooltip && linhasTooltip.length > 0
      ? (() => {
          const maiorNome = Math.max(...linhasTooltip.map((l) => l.nome.length))
          const largura = Math.min(260, Math.max(150, 58 + maiorNome * 5.4))
          const altura = 24 + linhasTooltip.length * 15
          const xPonto = x(hoverIndice)
          const estouraDireita = xPonto + 14 + largura > LARG - 6
          const rectX = estouraDireita ? xPonto - 14 - largura : xPonto + 14
          const rectY = MARG.topo + 4
          return { rectX, rectY, largura, altura, textX: rectX + 10, mes: NOMES_MES[hoverIndice], linhas: linhasTooltip }
        })()
      : null

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
              <input
                type="radio"
                name="serie-ano-ano"
                checked={chaveSelecionada === l.item.chave}
                onChange={() => setChaveSelecionada(l.item.chave)}
              />
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
                {NOMES_MES[i]}
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

            {hoverIndice !== null && (
              <line x1={x(hoverIndice)} x2={x(hoverIndice)} y1={MARG.topo} y2={ALT - MARG.base} className="comparador-linha-guia" />
            )}

            {mesesDoAno.map((_, i) => (
              <rect
                key={`banda-${i}`}
                x={x(i) - espacamento / 2}
                y={MARG.topo}
                width={espacamento}
                height={ALT_PLOT}
                fill="transparent"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoverIndice(i)}
                onMouseLeave={() => setHoverIndice(null)}
              />
            ))}

            {tooltip && (
              <g>
                <rect x={tooltip.rectX} y={tooltip.rectY} width={tooltip.largura} height={tooltip.altura} rx={6} fill="var(--cor-superficie)" stroke="var(--cor-borda)" strokeWidth={1.5} />
                <text x={tooltip.textX} y={tooltip.rectY + 15} className="comparador-tooltip-titulo" fill="var(--cor-texto)">
                  {tooltip.mes}
                </text>
                {tooltip.linhas.map((l, i) => (
                  <g key={i}>
                    <rect x={tooltip.textX} y={tooltip.rectY + 23 + i * 15 - 7} width={8} height={8} rx={2} fill={l.cor} />
                    <text x={tooltip.textX + 13} y={tooltip.rectY + 23 + i * 15} className="comparador-tooltip-texto">
                      {l.nome}: {l.valor}
                    </text>
                  </g>
                ))}
              </g>
            )}
          </svg>
        )}
      </div>
    </div>
  )
}
