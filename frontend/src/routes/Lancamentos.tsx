import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import '../components/crud.css'
import '../components/forms.css'
import '../components/lancamentos.css'
import '../components/resumoCards.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarData, formatarMoeda } from '../lib/formatar'
import { usePrivacidade } from '../lib/PrivacyContext'
import {
  ESTRUTURAS,
  MEIOS_PAGAMENTO,
  TIPOS_MOVIMENTO,
  TIPO_CATEGORIA_ESPERADO,
  rotuloEstruturaCusto,
  rotuloMeioPagamento,
  rotuloTipoMovimento,
} from '../lib/rotulos'
import type {
  Caixinha,
  Categoria,
  Conta,
  EstruturaCusto,
  MeioPagamento,
  ResumoLancamentos,
  Subcategoria,
  Transacao,
  TipoMovimento,
} from '../lib/types'

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

const EXPLICACAO_RESUMO: Record<string, string> = {
  total: 'Quantidade de lançamentos que batem com os filtros aplicados.',
  receitas: 'Soma de todos os lançamentos do tipo Receita no período filtrado.',
  despesas_liquidas: 'Despesas menos estornos/ressarcimentos vinculados a elas — o quanto de fato saiu do bolso.',
  fluxo_caixa: 'Receitas menos despesas brutas (sem descontar estornos) — o que de fato entrou e saiu das contas.',
  taxa_poupanca: 'Percentual da receita (já somando ajustes soltos) que sobrou depois das despesas líquidas.',
}

// último dia do mês (JS: dia 0 do mês seguinte)
function ultimoDiaDoMes(ano: number, mesIndice: number): number {
  return new Date(ano, mesIndice + 1, 0).getDate()
}

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

type Filtros = {
  tipoMovimento: TipoMovimento | ''
  categoriaId: string
  subcategoriaId: string
  contaId: string
  caixinhaId: string
  estruturaCusto: EstruturaCusto | ''
  meioPagamento: MeioPagamento | ''
  dataInicio: string
  dataFim: string
  descricao: string
}

const FILTROS_VAZIOS: Filtros = {
  tipoMovimento: '',
  categoriaId: '',
  subcategoriaId: '',
  contaId: '',
  caixinhaId: '',
  estruturaCusto: '',
  meioPagamento: '',
  dataInicio: '',
  dataFim: '',
  descricao: '',
}

// aplicação/retirada em caixinha é reserva, sem cor especial (fica no
// texto padrão); só quando é investimento de verdade (categoria
// investimento, sem caixinha) fica azul — ver Estrutura de Custo, mesma
// distinção de bucket "reservas" vs "investimentos"
function classeValor(transacao: Transacao): string {
  const { tipo_movimento: tipo, caixinha_id: caixinhaId } = transacao
  if (tipo === 'receita' || tipo === 'estorno' || tipo === 'ressarcimento') return 'valor-receita'
  if (tipo === 'despesa') return 'valor-despesa'
  if ((tipo === 'aplicacao' || tipo === 'retirada') && !caixinhaId) return 'valor-investimento'
  return ''
}

export function Lancamentos() {
  const { oculto } = usePrivacidade()
  const [contas, setContas] = useState<Conta[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [erroCarga, setErroCarga] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      apiFetch<Conta[]>('/contas'),
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Caixinha[]>('/caixinhas'),
    ])
      .then(([c, cat, sub, cx]) => {
        setContas(c)
        setCategorias(cat)
        setSubcategorias(sub)
        setCaixinhas(cx)
      })
      .catch((e) => setErroCarga(e instanceof ApiError ? e.message : 'Falha ao carregar dados de apoio'))
  }, [])

  const contasPorId = useMemo(() => new Map(contas.map((c) => [c.id, c])), [contas])
  const categoriasPorId = useMemo(() => new Map(categorias.map((c) => [c.id, c])), [categorias])
  const subcategoriasPorId = useMemo(() => new Map(subcategorias.map((s) => [s.id, s])), [subcategorias])
  const caixinhasPorId = useMemo(() => new Map(caixinhas.map((c) => [c.id, c])), [caixinhas])

  const [filtros, setFiltros] = useState<Filtros>(FILTROS_VAZIOS)
  const [mesRapido, setMesRapido] = useState('')
  const [anoRapido, setAnoRapido] = useState(String(new Date().getFullYear()))

  // drill-down vindo de outra tela (ex: Estrutura de Custo) — lê uma vez na
  // montagem; categoria_id/subcategoria_id/mes (YYYY-MM) na URL
  const [searchParams] = useSearchParams()
  useEffect(() => {
    const categoriaId = searchParams.get('categoria_id')
    const subcategoriaId = searchParams.get('subcategoria_id')
    const mes = searchParams.get('mes')
    if (!categoriaId && !subcategoriaId && !mes) return
    setFiltros((atual) => {
      const proximo = { ...atual }
      if (categoriaId) proximo.categoriaId = categoriaId
      if (subcategoriaId) proximo.subcategoriaId = subcategoriaId
      if (mes) {
        const [ano, mesNum] = mes.split('-').map(Number)
        proximo.dataInicio = `${ano}-${pad2(mesNum)}-01`
        proximo.dataFim = `${ano}-${pad2(mesNum)}-${pad2(ultimoDiaDoMes(ano, mesNum - 1))}`
      }
      return proximo
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const categoriasFiltro = useMemo(() => {
    if (!filtros.tipoMovimento) return categorias
    return categorias.filter((c) => c.tipo === TIPO_CATEGORIA_ESPERADO[filtros.tipoMovimento as TipoMovimento])
  }, [categorias, filtros.tipoMovimento])

  const subcategoriasFiltro = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === filtros.categoriaId),
    [subcategorias, filtros.categoriaId],
  )

  const anosDisponiveis = useMemo(() => {
    const atual = new Date().getFullYear()
    return Array.from({ length: 6 }, (_, i) => atual - 4 + i)
  }, [])

  function atualizarFiltro<K extends keyof Filtros>(campo: K, valor: Filtros[K]) {
    setMesRapido('')
    setFiltros((atual) => {
      const proximo = { ...atual, [campo]: valor }
      if (campo === 'tipoMovimento') {
        proximo.categoriaId = ''
        proximo.subcategoriaId = ''
      }
      if (campo === 'categoriaId') {
        proximo.subcategoriaId = ''
      }
      return proximo
    })
  }

  // recebe o ano como parâmetro em vez de ler `anoRapido` do escopo — trocar
  // ano e mês quase juntos (o clique no Ano dispara isso antes do
  // setAnoRapido de cima re-renderizar) pegaria o valor antigo do estado
  function aplicarMesRapido(mesIndice: string, ano = Number(anoRapido)) {
    setMesRapido(mesIndice)
    if (mesIndice === '') return
    const mes = Number(mesIndice)
    setFiltros((atual) => ({
      ...atual,
      dataInicio: `${ano}-${pad2(mes + 1)}-01`,
      dataFim: `${ano}-${pad2(mes + 1)}-${pad2(ultimoDiaDoMes(ano, mes))}`,
    }))
  }

  const [transacoes, setTransacoes] = useState<Transacao[] | null>(null)
  const [resumo, setResumo] = useState<ResumoLancamentos | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [excluindoId, setExcluindoId] = useState<string | null>(null)

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (filtros.tipoMovimento) params.set('tipo_movimento', filtros.tipoMovimento)
    if (filtros.categoriaId) params.set('categoria_id', filtros.categoriaId)
    if (filtros.subcategoriaId) params.set('subcategoria_id', filtros.subcategoriaId)
    if (filtros.contaId) params.set('conta_id', filtros.contaId)
    if (filtros.caixinhaId) params.set('caixinha_id', filtros.caixinhaId)
    if (filtros.estruturaCusto) params.set('estrutura_custo', filtros.estruturaCusto)
    if (filtros.meioPagamento) params.set('meio_pagamento', filtros.meioPagamento)
    if (filtros.dataInicio) params.set('data_inicio', filtros.dataInicio)
    if (filtros.dataFim) params.set('data_fim', filtros.dataFim)
    if (filtros.descricao.trim()) params.set('descricao', filtros.descricao.trim())
    return params.toString()
  }, [filtros])

  // guarda contra corrida: se o filtro mudar de novo antes da resposta
  // anterior voltar, essa resposta desatualizada (de um filtro mais largo,
  // por exemplo) não pode sobrescrever o resultado do filtro atual
  const ultimaRequisicao = useRef(0)

  function carregar() {
    const idRequisicao = ++ultimaRequisicao.current
    setErro(null)
    Promise.all([
      apiFetch<Transacao[]>(`/transacoes${queryString ? `?${queryString}` : ''}`),
      apiFetch<ResumoLancamentos>(`/transacoes/resumo${queryString ? `?${queryString}` : ''}`),
    ])
      .then(([lista, res]) => {
        if (idRequisicao !== ultimaRequisicao.current) return
        setTransacoes(lista)
        setResumo(res)
      })
      .catch((e) => {
        if (idRequisicao !== ultimaRequisicao.current) return
        setErro(e instanceof ApiError ? e.message : 'Falha ao buscar lançamentos')
      })
  }

  // debounce: espera parar de trocar filtro (ou digitar na descrição) antes de consultar a API
  useEffect(() => {
    const timer = setTimeout(carregar, 300)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryString])

  async function excluir(transacao: Transacao) {
    const rotulo = transacao.descricao ?? `${rotuloTipoMovimento(transacao.tipo_movimento)} de ${formatarMoeda(transacao.valor)}`
    if (!window.confirm(`Excluir o lançamento "${rotulo}"? Essa ação não pode ser desfeita.`)) return
    setExcluindoId(transacao.id)
    try {
      await apiFetch(`/transacoes/${transacao.id}`, { method: 'DELETE' })
      carregar()
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao excluir lançamento')
    } finally {
      setExcluindoId(null)
    }
  }

  if (erroCarga) {
    return <p className="mensagem-erro">{erroCarga}</p>
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Lançamentos</h1>

      {resumo && (
        <div className="resumo-cards">
          <div className="resumo-card" title={EXPLICACAO_RESUMO.total}>
            <span className="resumo-card-rotulo">Lançamentos</span>
            <span className="resumo-card-valor">{resumo.total_lancamentos}</span>
          </div>
          <div className="resumo-card" title={EXPLICACAO_RESUMO.receitas}>
            <span className="resumo-card-rotulo">Receitas</span>
            <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas, oculto)}</span>
          </div>
          <div className="resumo-card" title={EXPLICACAO_RESUMO.despesas_liquidas}>
            <span className="resumo-card-rotulo">Despesas líquidas</span>
            <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas, oculto)}</span>
          </div>
          <div className="resumo-card" title={EXPLICACAO_RESUMO.fluxo_caixa}>
            <span className="resumo-card-rotulo">Fluxo de caixa</span>
            <span className={`resumo-card-valor ${resumo.resultado_fluxo_caixa >= 0 ? 'valor-receita' : 'valor-despesa'}`}>
              {formatarMoeda(resumo.resultado_fluxo_caixa, oculto)}
            </span>
          </div>
          <div className="resumo-card" title={EXPLICACAO_RESUMO.taxa_poupanca}>
            <span className="resumo-card-rotulo">Taxa de poupança</span>
            <span className="resumo-card-valor">
              {resumo.taxa_poupanca === null ? '—' : `${resumo.taxa_poupanca.toFixed(1)}%`}
            </span>
          </div>
        </div>
      )}

      <div className="filtros">
        <div className="filtros-linha">
          <label className="campo">
            Tipo
            <select
              value={filtros.tipoMovimento}
              onChange={(e) => atualizarFiltro('tipoMovimento', e.target.value as TipoMovimento | '')}
            >
              <option value="">Todos</option>
              {TIPOS_MOVIMENTO.map((t) => (
                <option key={t.valor} value={t.valor}>
                  {t.rotulo}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Descrição
            <input
              type="text"
              placeholder="Buscar por texto…"
              value={filtros.descricao}
              onChange={(e) => atualizarFiltro('descricao', e.target.value)}
            />
          </label>
          <label className="campo">
            Mês
            <select value={mesRapido} onChange={(e) => aplicarMesRapido(e.target.value)}>
              <option value="">Personalizado</option>
              {MESES.map((nome, indice) => (
                <option key={nome} value={indice}>
                  {nome}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Ano
            <select
              value={anoRapido}
              onChange={(e) => {
                setAnoRapido(e.target.value)
                if (mesRapido !== '') aplicarMesRapido(mesRapido, Number(e.target.value))
              }}
            >
              {anosDisponiveis.map((ano) => (
                <option key={ano} value={ano}>
                  {ano}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filtros-linha">
          <label className="campo">
            De
            <input type="date" value={filtros.dataInicio} onChange={(e) => atualizarFiltro('dataInicio', e.target.value)} />
          </label>
          <label className="campo">
            Até
            <input type="date" value={filtros.dataFim} onChange={(e) => atualizarFiltro('dataFim', e.target.value)} />
          </label>
          <label className="campo">
            Conta
            <select value={filtros.contaId} onChange={(e) => atualizarFiltro('contaId', e.target.value)}>
              <option value="">Todas</option>
              {contas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Caixinha
            <select value={filtros.caixinhaId} onChange={(e) => atualizarFiltro('caixinhaId', e.target.value)}>
              <option value="">Todas</option>
              {caixinhas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filtros-linha">
          <label className="campo">
            Categoria
            <select value={filtros.categoriaId} onChange={(e) => atualizarFiltro('categoriaId', e.target.value)}>
              <option value="">Todas</option>
              {categoriasFiltro.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Subcategoria
            <select
              value={filtros.subcategoriaId}
              onChange={(e) => atualizarFiltro('subcategoriaId', e.target.value)}
              disabled={!filtros.categoriaId}
            >
              <option value="">Todas</option>
              {subcategoriasFiltro.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Estrutura de custo
            <select
              value={filtros.estruturaCusto}
              onChange={(e) => atualizarFiltro('estruturaCusto', e.target.value as EstruturaCusto | '')}
            >
              <option value="">Todas</option>
              {ESTRUTURAS.map((e) => (
                <option key={e.valor} value={e.valor}>
                  {e.rotulo}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            Meio de pagamento
            <select
              value={filtros.meioPagamento}
              onChange={(e) => atualizarFiltro('meioPagamento', e.target.value as MeioPagamento | '')}
            >
              <option value="">Todos</option>
              {MEIOS_PAGAMENTO.map((m) => (
                <option key={m.valor} value={m.valor}>
                  {m.rotulo}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filtros-linha">
          <button
            type="button"
            className="botao-secundario"
            onClick={() => {
              setMesRapido('')
              setFiltros(FILTROS_VAZIOS)
            }}
          >
            Limpar filtros
          </button>
        </div>
      </div>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {transacoes === null && <p>Carregando…</p>}
      {transacoes?.length === 0 && <p>Nenhum lançamento encontrado com esses filtros.</p>}
      {transacoes && transacoes.length > 0 && (
        <ul className="lista-crud">
          {transacoes.map((t) => {
            const conta = contasPorId.get(t.conta_id)
            const categoria = t.categoria_id ? categoriasPorId.get(t.categoria_id) : undefined
            const subcategoria = t.subcategoria_id ? subcategoriasPorId.get(t.subcategoria_id) : undefined
            const caixinha = t.caixinha_id ? caixinhasPorId.get(t.caixinha_id) : undefined

            const detalhes = [
              rotuloTipoMovimento(t.tipo_movimento),
              conta?.nome,
              categoria?.nome,
              subcategoria?.nome,
              caixinha?.nome,
              t.estrutura_custo ? rotuloEstruturaCusto(t.estrutura_custo) : null,
              t.meio_pagamento ? rotuloMeioPagamento(t.meio_pagamento) : null,
              t.pagamento === 'parcelado' ? `parcela ${t.parcela_atual}/${t.parcela_total}` : null,
            ].filter(Boolean)

            return (
              <li key={t.id}>
                <div className="item-linha">
                  <div className="item-info">
                    <span className="item-titulo">
                      {formatarData(t.data_compra)} — {t.descricao ?? '(sem descrição)'}
                    </span>
                    <span className="item-detalhe">{detalhes.join(' — ')}</span>
                  </div>
                  <div className="item-acoes">
                    <span className={classeValor(t)} style={{ fontWeight: 600 }}>
                      {formatarMoeda(t.valor, oculto)}
                    </span>
                    {t.pagamento === 'avista' && (
                      <Link to={`/lancamentos/${t.id}/editar`} className="botao-link">
                        Editar
                      </Link>
                    )}
                    <button
                      type="button"
                      className="botao-link"
                      disabled={excluindoId === t.id}
                      onClick={() => excluir(t)}
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
