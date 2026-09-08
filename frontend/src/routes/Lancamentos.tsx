import { useEffect, useMemo, useState } from 'react'
import '../components/crud.css'
import '../components/forms.css'
import '../components/lancamentos.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarData, formatarMoeda } from '../lib/formatar'
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

const TIPOS_MOVIMENTO: { valor: TipoMovimento; rotulo: string }[] = [
  { valor: 'receita', rotulo: 'Receita' },
  { valor: 'despesa', rotulo: 'Despesa' },
  { valor: 'aplicacao', rotulo: 'Aplicação' },
  { valor: 'retirada', rotulo: 'Retirada' },
  { valor: 'estorno', rotulo: 'Estorno' },
  { valor: 'ressarcimento', rotulo: 'Ressarcimento' },
]

const ESTRUTURAS: { valor: EstruturaCusto; rotulo: string }[] = [
  { valor: 'fixo', rotulo: 'Fixo' },
  { valor: 'variavel', rotulo: 'Variável' },
  { valor: 'sazonal', rotulo: 'Sazonal' },
  { valor: 'investimentos', rotulo: 'Investimentos' },
]

const MEIOS_PAGAMENTO: { valor: MeioPagamento; rotulo: string }[] = [
  { valor: 'pix', rotulo: 'Pix' },
  { valor: 'cartao_debito', rotulo: 'Cartão de débito' },
  { valor: 'cartao_credito', rotulo: 'Cartão de crédito' },
  { valor: 'boleto', rotulo: 'Boleto' },
  { valor: 'debito_automatico', rotulo: 'Débito automático' },
  { valor: 'dinheiro', rotulo: 'Dinheiro' },
  { valor: 'transferencia', rotulo: 'Transferência' },
  { valor: 'outro', rotulo: 'Outro' },
]

// mesmo mapeamento de backend/app/routers/transacoes.py::_TIPO_CATEGORIA_ESPERADO
// — usado só pra restringir o <select> de categoria do filtro ao tipo certo
const TIPO_CATEGORIA_ESPERADO: Record<TipoMovimento, 'receita' | 'despesa' | 'investimento'> = {
  receita: 'receita',
  despesa: 'despesa',
  estorno: 'despesa',
  ressarcimento: 'despesa',
  aplicacao: 'investimento',
  retirada: 'investimento',
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

function rotuloTipoMovimento(tipo: TipoMovimento): string {
  return TIPOS_MOVIMENTO.find((t) => t.valor === tipo)?.rotulo ?? tipo
}

function classeValor(tipo: TipoMovimento): string {
  if (tipo === 'receita' || tipo === 'estorno' || tipo === 'ressarcimento') return 'valor-receita'
  if (tipo === 'despesa') return 'valor-despesa'
  return ''
}

export function Lancamentos() {
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

  const categoriasFiltro = useMemo(() => {
    if (!filtros.tipoMovimento) return categorias
    return categorias.filter((c) => c.tipo === TIPO_CATEGORIA_ESPERADO[filtros.tipoMovimento as TipoMovimento])
  }, [categorias, filtros.tipoMovimento])

  const subcategoriasFiltro = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === filtros.categoriaId),
    [subcategorias, filtros.categoriaId],
  )

  function atualizarFiltro<K extends keyof Filtros>(campo: K, valor: Filtros[K]) {
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

  function carregar() {
    setErro(null)
    Promise.all([
      apiFetch<Transacao[]>(`/transacoes${queryString ? `?${queryString}` : ''}`),
      apiFetch<ResumoLancamentos>(`/transacoes/resumo${queryString ? `?${queryString}` : ''}`),
    ])
      .then(([lista, res]) => {
        setTransacoes(lista)
        setResumo(res)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao buscar lançamentos'))
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
          <div className="resumo-card">
            <span className="resumo-card-rotulo">Lançamentos</span>
            <span className="resumo-card-valor">{resumo.total_lancamentos}</span>
          </div>
          <div className="resumo-card">
            <span className="resumo-card-rotulo">Receitas</span>
            <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas)}</span>
          </div>
          <div className="resumo-card">
            <span className="resumo-card-rotulo">Despesas líquidas</span>
            <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas)}</span>
          </div>
          <div className="resumo-card">
            <span className="resumo-card-rotulo">Fluxo de caixa</span>
            <span className={`resumo-card-valor ${resumo.resultado_fluxo_caixa >= 0 ? 'valor-receita' : 'valor-despesa'}`}>
              {formatarMoeda(resumo.resultado_fluxo_caixa)}
            </span>
          </div>
          <div className="resumo-card">
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
            De
            <input type="date" value={filtros.dataInicio} onChange={(e) => atualizarFiltro('dataInicio', e.target.value)} />
          </label>
          <label className="campo">
            Até
            <input type="date" value={filtros.dataFim} onChange={(e) => atualizarFiltro('dataFim', e.target.value)} />
          </label>
        </div>

        <div className="filtros-linha">
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
          <div className="campo" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="botao-secundario" onClick={() => setFiltros(FILTROS_VAZIOS)}>
              Limpar filtros
            </button>
          </div>
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
            const meioPagamento = MEIOS_PAGAMENTO.find((m) => m.valor === t.meio_pagamento)?.rotulo

            const detalhes = [
              rotuloTipoMovimento(t.tipo_movimento),
              conta?.nome,
              categoria?.nome,
              subcategoria?.nome,
              caixinha?.nome,
              meioPagamento,
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
                    <span className={classeValor(t.tipo_movimento)} style={{ fontWeight: 600 }}>
                      {formatarMoeda(t.valor)}
                    </span>
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
