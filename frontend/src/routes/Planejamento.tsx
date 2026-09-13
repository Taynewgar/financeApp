import { useEffect, useMemo, useState, type FormEvent } from 'react'
import '../components/forms.css'
import '../components/crud.css'
import '../components/planejamento.css'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoeda } from '../lib/formatar'
import { ordenarPorNome } from '../lib/ordenar'
import { usePrivacidade } from '../lib/PrivacyContext'
import type { Bucket, Categoria, Conta, Orcamento, OrcamentoItem, Subcategoria } from '../lib/types'

const BUCKETS: {
  valor: Bucket
  rotulo: string
  cor: string
  limiteCampo: 'limite_custos_fixos' | 'limite_custos_variaveis' | 'limite_sazonalidades' | 'limite_investimentos'
}[] = [
  { valor: 'custos_fixos', rotulo: 'Custos Fixos', cor: 'var(--bucket-fixos)', limiteCampo: 'limite_custos_fixos' },
  {
    valor: 'custos_variaveis',
    rotulo: 'Custos Variáveis',
    cor: 'var(--bucket-variaveis)',
    limiteCampo: 'limite_custos_variaveis',
  },
  {
    valor: 'sazonalidades',
    rotulo: 'Sazonalidades',
    cor: 'var(--bucket-sazonalidades)',
    limiteCampo: 'limite_sazonalidades',
  },
  {
    valor: 'investimentos',
    rotulo: 'Investimentos',
    cor: 'var(--bucket-investimentos)',
    limiteCampo: 'limite_investimentos',
  },
]

type FormConfig = {
  receita_base: string
  percentual_geral: string
  limite_custos_fixos: string
  limite_custos_variaveis: string
  limite_sazonalidades: string
  limite_investimentos: string
}

const FORM_CONFIG_PADRAO: FormConfig = {
  receita_base: '',
  percentual_geral: '100',
  limite_custos_fixos: '40',
  limite_custos_variaveis: '25',
  limite_sazonalidades: '10',
  limite_investimentos: '25',
}

type FormItem = {
  categoria_id: string
  subcategoria_id: string
  nome: string
  conta_vinculada_id: string
  orcamento_mensal: string
}

const FORM_ITEM_VAZIO: FormItem = { categoria_id: '', subcategoria_id: '', nome: '', conta_vinculada_id: '', orcamento_mensal: '' }

function hojeAnoMes(): string {
  return new Date().toISOString().slice(0, 7)
}

/** 'YYYY-MM' menos N meses, sempre 'YYYY-MM' de volta. */
function mesesAntes(anoMes: string, n: number): string {
  const [ano, mes] = anoMes.split('-').map(Number)
  const totalMeses = ano * 12 + (mes - 1) - n
  const anoResultado = Math.floor(totalMeses / 12)
  const mesResultado = (totalMeses % 12) + 1
  return `${anoResultado}-${String(mesResultado).padStart(2, '0')}`
}

/** Mesma conta de backend/app/services/orcamento_teto.py — teto "puro" em
 * R$ do bucket, sem somar sobra de envelope de mês anterior. */
function tetoBucket(
  orcamento: Orcamento,
  limiteCampo: 'limite_custos_fixos' | 'limite_custos_variaveis' | 'limite_sazonalidades' | 'limite_investimentos',
): number {
  const baseOrcada = (orcamento.receita_base * orcamento.percentual_geral) / 100
  const limite = orcamento[limiteCampo]
  return Math.round(((baseOrcada * limite) / 100) * 100) / 100
}

function rotuloItem(item: OrcamentoItem, categorias: Categoria[], subcategorias: Subcategoria[], contas: Conta[]): string {
  if (item.subcategoria_id) return subcategorias.find((s) => s.id === item.subcategoria_id)?.nome ?? 'Subcategoria removida'
  if (item.categoria_id) return categorias.find((c) => c.id === item.categoria_id)?.nome ?? 'Categoria removida'
  if (item.conta_vinculada_id) return contas.find((c) => c.id === item.conta_vinculada_id)?.nome ?? 'Conta removida'
  return item.nome ?? 'Item sem nome'
}

export function Planejamento() {
  const { oculto } = usePrivacidade()
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [orcamentos, setOrcamentos] = useState<Orcamento[] | null>(null)
  const [itens, setItens] = useState<OrcamentoItem[] | null>(null)
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [contas, setContas] = useState<Conta[]>([])
  const [erro, setErro] = useState<string | null>(null)

  const [mostrarFormConfig, setMostrarFormConfig] = useState(false)
  const [formConfig, setFormConfig] = useState<FormConfig>(FORM_CONFIG_PADRAO)
  const [itemFormAberto, setItemFormAberto] = useState<Bucket | null>(null)
  const [itemEditando, setItemEditando] = useState<OrcamentoItem | null>(null)
  const [formItem, setFormItem] = useState<FormItem>(FORM_ITEM_VAZIO)
  const [salvando, setSalvando] = useState(false)
  const [gerandoProximoMes, setGerandoProximoMes] = useState(false)

  useEffect(() => {
    Promise.all([
      apiFetch<Orcamento[]>('/orcamentos'),
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Conta[]>('/contas'),
    ])
      .then(([o, cat, sub, c]) => {
        setOrcamentos(o)
        setCategorias(ordenarPorNome(cat.filter((x) => x.ativo)))
        setSubcategorias(ordenarPorNome(sub.filter((x) => x.ativo)))
        setContas(ordenarPorNome(c.filter((x) => x.ativo)))
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o planejamento'))
  }, [])

  const orcamentoAtual = useMemo(
    () => orcamentos?.find((o) => o.vigencia_mes.slice(0, 7) === vigenciaMes) ?? null,
    [orcamentos, vigenciaMes],
  )
  const orcamentoMesAnterior = useMemo(
    () => orcamentos?.find((o) => o.vigencia_mes.slice(0, 7) === mesesAntes(vigenciaMes, 1)) ?? null,
    [orcamentos, vigenciaMes],
  )

  useEffect(() => {
    if (!orcamentoAtual) {
      setItens([])
      return
    }
    apiFetch<OrcamentoItem[]>(`/orcamentos/${orcamentoAtual.id}/itens`)
      .then(setItens)
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar os itens do orçamento'))
  }, [orcamentoAtual])

  function iniciarCriacaoConfig() {
    setFormConfig(FORM_CONFIG_PADRAO)
    setMostrarFormConfig(true)
  }

  function iniciarEdicaoConfig() {
    if (!orcamentoAtual) return
    setFormConfig({
      receita_base: String(orcamentoAtual.receita_base),
      percentual_geral: String(orcamentoAtual.percentual_geral),
      limite_custos_fixos: String(orcamentoAtual.limite_custos_fixos),
      limite_custos_variaveis: String(orcamentoAtual.limite_custos_variaveis),
      limite_sazonalidades: String(orcamentoAtual.limite_sazonalidades),
      limite_investimentos: String(orcamentoAtual.limite_investimentos),
    })
    setMostrarFormConfig(true)
  }

  async function handleSubmitConfig(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const payload = {
        receita_base: Number(formConfig.receita_base) || 0,
        percentual_geral: Number(formConfig.percentual_geral) || 0,
        limite_custos_fixos: Number(formConfig.limite_custos_fixos) || 0,
        limite_custos_variaveis: Number(formConfig.limite_custos_variaveis) || 0,
        limite_sazonalidades: Number(formConfig.limite_sazonalidades) || 0,
        limite_investimentos: Number(formConfig.limite_investimentos) || 0,
      }
      if (orcamentoAtual) {
        const atualizado = await apiFetch<Orcamento>(`/orcamentos/${orcamentoAtual.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setOrcamentos((atual) => atual!.map((o) => (o.id === atualizado.id ? atualizado : o)))
      } else {
        const criado = await apiFetch<Orcamento>('/orcamentos', {
          method: 'POST',
          body: JSON.stringify({ vigencia_mes: `${vigenciaMes}-01`, ...payload }),
        })
        setOrcamentos((atual) => [...(atual ?? []), criado])
      }
      setMostrarFormConfig(false)
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar orçamento')
    } finally {
      setSalvando(false)
    }
  }

  async function gerarAPartirDoAnterior() {
    if (!orcamentoMesAnterior) return
    setGerandoProximoMes(true)
    setErro(null)
    try {
      const novo = await apiFetch<Orcamento>(`/orcamentos/${orcamentoMesAnterior.id}/proximo-mes`, { method: 'POST' })
      setOrcamentos((atual) => [...(atual ?? []), novo])
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao gerar orçamento')
    } finally {
      setGerandoProximoMes(false)
    }
  }

  async function gerarProximoMes() {
    if (!orcamentoAtual) return
    setGerandoProximoMes(true)
    setErro(null)
    try {
      const novo = await apiFetch<Orcamento>(`/orcamentos/${orcamentoAtual.id}/proximo-mes`, { method: 'POST' })
      setOrcamentos((atual) => [...(atual ?? []), novo])
      setVigenciaMes(novo.vigencia_mes.slice(0, 7))
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao gerar orçamento')
    } finally {
      setGerandoProximoMes(false)
    }
  }

  function iniciarCriacaoItem(bucket: Bucket) {
    setFormItem(FORM_ITEM_VAZIO)
    setItemEditando(null)
    setItemFormAberto(bucket)
  }

  function iniciarEdicaoItem(item: OrcamentoItem) {
    setFormItem({
      categoria_id: item.categoria_id ?? '',
      subcategoria_id: item.subcategoria_id ?? '',
      nome: item.nome ?? '',
      conta_vinculada_id: item.conta_vinculada_id ?? '',
      orcamento_mensal: String(item.orcamento_mensal),
    })
    setItemEditando(item)
    setItemFormAberto(item.bucket)
  }

  async function toggleAtivoItem(item: OrcamentoItem) {
    if (!orcamentoAtual) return
    try {
      const atualizado = await apiFetch<OrcamentoItem>(
        `/orcamentos/${orcamentoAtual.id}/itens/${item.id}/ativo?ativo=${!item.ativo}`,
        { method: 'PATCH' },
      )
      setItens((atual) => atual!.map((i) => (i.id === atualizado.id ? atualizado : i)))
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao atualizar item')
    }
  }

  async function handleSubmitItem(event: FormEvent, bucket: Bucket) {
    event.preventDefault()
    if (!orcamentoAtual) return
    setSalvando(true)
    setErro(null)
    try {
      const payload = {
        bucket,
        categoria_id: formItem.categoria_id || null,
        subcategoria_id: formItem.subcategoria_id || null,
        nome: formItem.nome || null,
        conta_vinculada_id: formItem.conta_vinculada_id || null,
        orcamento_mensal: Number(formItem.orcamento_mensal) || 0,
      }
      if (itemEditando) {
        const atualizado = await apiFetch<OrcamentoItem>(`/orcamentos/${orcamentoAtual.id}/itens/${itemEditando.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setItens((atual) => atual!.map((i) => (i.id === atualizado.id ? atualizado : i)))
      } else {
        const criado = await apiFetch<OrcamentoItem>(`/orcamentos/${orcamentoAtual.id}/itens`, {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setItens((atual) => [...(atual ?? []), criado])
      }
      setItemFormAberto(null)
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar item')
    } finally {
      setSalvando(false)
    }
  }

  const somaLimites = orcamentoAtual ? BUCKETS.reduce((soma, b) => soma + orcamentoAtual[b.limiteCampo], 0) : 0
  const disponivelMensal = orcamentoAtual ? (orcamentoAtual.receita_base * orcamentoAtual.percentual_geral) / 100 : 0

  return (
    <div className="planejamento">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 2 }}>Planejamento</h1>
          <p className="planejamento-resumo" style={{ margin: 0 }}>
            Defina os valores-alvo do orçamento — a leitura do que foi de fato gasto fica na Estrutura de Custo.
          </p>
        </div>
        <label className="campo" style={{ maxWidth: 180 }}>
          Mês
          <input type="month" value={vigenciaMes} onChange={(e) => setVigenciaMes(e.target.value)} />
        </label>
      </div>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {orcamentos === null && <p>Carregando…</p>}

      {orcamentos !== null && !orcamentoAtual && !mostrarFormConfig && (
        <div style={{ marginTop: 16 }}>
          <p>Nenhum orçamento configurado para este mês.</p>
          <div className="form-acoes">
            {orcamentoMesAnterior && (
              <button type="button" className="botao-primario" onClick={gerarAPartirDoAnterior} disabled={gerandoProximoMes}>
                {gerandoProximoMes ? 'Gerando…' : `Gerar a partir de ${mesesAntes(vigenciaMes, 1)} (traz a sobra do envelope)`}
              </button>
            )}
            <button type="button" className="botao-secundario" onClick={iniciarCriacaoConfig}>
              Criar do zero
            </button>
          </div>
        </div>
      )}

      {mostrarFormConfig && (
        <form className="form" onSubmit={handleSubmitConfig} style={{ marginTop: 16, marginBottom: 20, maxWidth: 560 }}>
          <div className="campo-linha">
            <label className="campo">
              Renda base (R$)
              <input
                type="number"
                min={0}
                step="0.01"
                required
                value={formConfig.receita_base}
                onChange={(e) => setFormConfig({ ...formConfig, receita_base: e.target.value })}
              />
            </label>
            <label className="campo">
              % destinado ao orçamento
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                required
                value={formConfig.percentual_geral}
                onChange={(e) => setFormConfig({ ...formConfig, percentual_geral: e.target.value })}
              />
            </label>
          </div>
          <div className="campo-linha">
            <label className="campo">
              Limite Fixos (%)
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                required
                value={formConfig.limite_custos_fixos}
                onChange={(e) => setFormConfig({ ...formConfig, limite_custos_fixos: e.target.value })}
              />
            </label>
            <label className="campo">
              Limite Variáveis (%)
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                required
                value={formConfig.limite_custos_variaveis}
                onChange={(e) => setFormConfig({ ...formConfig, limite_custos_variaveis: e.target.value })}
              />
            </label>
          </div>
          <div className="campo-linha">
            <label className="campo">
              Limite Sazonalidades (%)
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                required
                value={formConfig.limite_sazonalidades}
                onChange={(e) => setFormConfig({ ...formConfig, limite_sazonalidades: e.target.value })}
              />
            </label>
            <label className="campo">
              Limite Investimentos (%)
              <input
                type="number"
                min={0}
                max={100}
                step="0.1"
                required
                value={formConfig.limite_investimentos}
                onChange={(e) => setFormConfig({ ...formConfig, limite_investimentos: e.target.value })}
              />
            </label>
          </div>
          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={salvando}>
              {salvando ? 'Salvando…' : orcamentoAtual ? 'Salvar alterações' : 'Criar orçamento'}
            </button>
            <button type="button" className="botao-secundario" onClick={() => setMostrarFormConfig(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {orcamentoAtual && !mostrarFormConfig && (
        <>
          <div className="planejamento-config-resumo">
            <p className="planejamento-resumo" style={{ margin: 0 }}>
              Renda base {formatarMoeda(orcamentoAtual.receita_base, oculto)} · {orcamentoAtual.percentual_geral}%
              destinado ao orçamento · disponível mensal {formatarMoeda(disponivelMensal, oculto)}
            </p>
            <button type="button" className="botao-secundario" onClick={iniciarEdicaoConfig}>
              Editar configuração
            </button>
          </div>

          <div className="planejamento-alocacao">
            <div className="planejamento-alocacao-cabecalho">
              <strong>Alocação total dos buckets</strong>
              <span className={somaLimites > 100 ? 'planejamento-estouro' : undefined}>
                {somaLimites.toFixed(0)}% de 100%{somaLimites > 100 && ' — acima de 100%'}
              </span>
            </div>
            <div className={`planejamento-alocacao-barra${somaLimites > 100 ? ' planejamento-alocacao-barra-estourada' : ''}`}>
              {BUCKETS.map(
                (b) =>
                  orcamentoAtual[b.limiteCampo] > 0 && (
                    <div
                      key={b.valor}
                      className="planejamento-alocacao-segmento"
                      style={{ width: `${(orcamentoAtual[b.limiteCampo] / Math.max(somaLimites, 100)) * 100}%`, background: b.cor }}
                      title={`${b.rotulo}: ${orcamentoAtual[b.limiteCampo]}%`}
                    />
                  ),
              )}
            </div>
            <div className="planejamento-alocacao-legenda">
              {BUCKETS.map((b) => (
                <span key={b.valor} className="planejamento-alocacao-legenda-item">
                  <span className="planejamento-swatch" style={{ background: b.cor }} /> {b.rotulo}{' '}
                  {orcamentoAtual[b.limiteCampo]}%
                </span>
              ))}
              {somaLimites < 100 && <span>{(100 - somaLimites).toFixed(0)}% ainda não alocado</span>}
              {somaLimites > 100 && (
                <span className="planejamento-estouro">
                  {(somaLimites - 100).toFixed(0)}% acima de 100% — reduza o limite de algum bucket
                </span>
              )}
            </div>
          </div>

          <div className="planejamento-buckets">
            {BUCKETS.map((b) => {
              const itensDoBucket = (itens ?? []).filter((i) => i.bucket === b.valor)
              const itensAtivos = itensDoBucket.filter((i) => i.ativo)
              const teto = tetoBucket(orcamentoAtual, b.limiteCampo)
              const somaAlocada = itensAtivos.reduce((soma, i) => soma + i.orcamento_mensal, 0)
              const percentualUso = teto > 0 ? Math.min(100, (somaAlocada / teto) * 100) : 0
              const estourou = somaAlocada > teto + 0.005
              const categoriasDoBucket = categorias.filter((c) =>
                b.valor === 'investimentos' ? c.tipo === 'investimento' : c.tipo === 'despesa',
              )
              const subcategoriasDaCategoria = subcategorias.filter((s) => s.categoria_id === formItem.categoria_id)

              return (
                <div key={b.valor} className="planejamento-bucket">
                  <div className="planejamento-bucket-cabecalho">
                    <h3>{b.rotulo}</h3>
                    <span className="planejamento-bucket-limite">limite {orcamentoAtual[b.limiteCampo]}%</span>
                  </div>
                  <div className="planejamento-progresso">
                    <div
                      className="planejamento-progresso-fill"
                      style={{ width: `${percentualUso}%`, background: estourou ? 'var(--cor-perigo)' : b.cor }}
                    />
                  </div>
                  <p className="planejamento-progresso-texto">
                    {formatarMoeda(somaAlocada, oculto)} alocado de {formatarMoeda(teto, oculto)} do teto
                    {estourou && ' — acima do teto'}
                  </p>

                  {itensDoBucket.length === 0 && (
                    <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13 }}>Nenhum item ainda.</p>
                  )}
                  {itensDoBucket.length > 0 && (
                    <ul className="lista-crud">
                      {itensDoBucket.map((item) => (
                        <li key={item.id} className={item.ativo ? '' : 'item-inativo'}>
                          <div className="item-linha">
                            <div className="item-info">
                              <span className="item-titulo">{rotuloItem(item, categorias, subcategorias, contas)}</span>
                              <span className="item-detalhe">
                                {formatarMoeda(item.orcamento_mensal, oculto)}
                                {item.saldo_anterior !== 0 &&
                                  ` · sobra do envelope: ${formatarMoeda(item.saldo_anterior, oculto)} · disponível: ${formatarMoeda(item.disponivel, oculto)}`}
                                {!item.ativo && ' — inativo'}
                              </span>
                            </div>
                            <div className="item-acoes">
                              <button type="button" className="botao-link" onClick={() => iniciarEdicaoItem(item)}>
                                Editar
                              </button>
                              <button type="button" className="botao-link" onClick={() => toggleAtivoItem(item)}>
                                {item.ativo ? 'Desativar' : 'Reativar'}
                              </button>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}

                  {itemFormAberto === b.valor ? (
                    <form className="form" onSubmit={(e) => handleSubmitItem(e, b.valor)} style={{ marginTop: 12 }}>
                      <div className="campo-linha">
                        <label className="campo">
                          Categoria
                          <select
                            value={formItem.categoria_id}
                            onChange={(e) => setFormItem({ ...formItem, categoria_id: e.target.value, subcategoria_id: '' })}
                          >
                            <option value="">Nenhuma</option>
                            {categoriasDoBucket.map((c) => (
                              <option key={c.id} value={c.id}>
                                {c.nome}
                              </option>
                            ))}
                          </select>
                        </label>
                        {formItem.categoria_id && (
                          <label className="campo">
                            Subcategoria
                            <select
                              value={formItem.subcategoria_id}
                              onChange={(e) => setFormItem({ ...formItem, subcategoria_id: e.target.value })}
                            >
                              <option value="">Nenhuma</option>
                              {subcategoriasDaCategoria.map((s) => (
                                <option key={s.id} value={s.id}>
                                  {s.nome}
                                </option>
                              ))}
                            </select>
                          </label>
                        )}
                      </div>
                      <div className="campo-linha">
                        <label className="campo">
                          Nome livre
                          <input
                            type="text"
                            placeholder="usado se não tiver categoria"
                            value={formItem.nome}
                            onChange={(e) => setFormItem({ ...formItem, nome: e.target.value })}
                          />
                        </label>
                        {b.valor === 'investimentos' && (
                          <label className="campo">
                            Conta vinculada
                            <select
                              value={formItem.conta_vinculada_id}
                              onChange={(e) => setFormItem({ ...formItem, conta_vinculada_id: e.target.value })}
                            >
                              <option value="">Nenhuma</option>
                              {contas.map((c) => (
                                <option key={c.id} value={c.id}>
                                  {c.nome}
                                </option>
                              ))}
                            </select>
                          </label>
                        )}
                      </div>
                      <label className="campo" style={{ maxWidth: 200 }}>
                        Valor mensal (R$)
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          required
                          value={formItem.orcamento_mensal}
                          onChange={(e) => setFormItem({ ...formItem, orcamento_mensal: e.target.value })}
                        />
                      </label>
                      <div className="form-acoes">
                        <button type="submit" className="botao-primario" disabled={salvando}>
                          {salvando ? 'Salvando…' : itemEditando ? 'Salvar alterações' : 'Criar item'}
                        </button>
                        <button type="button" className="botao-secundario" onClick={() => setItemFormAberto(null)}>
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <button type="button" className="botao-link" onClick={() => iniciarCriacaoItem(b.valor)}>
                      + Novo item
                    </button>
                  )}
                </div>
              )
            })}
          </div>

          <button type="button" className="botao-secundario" onClick={gerarProximoMes} disabled={gerandoProximoMes}>
            {gerandoProximoMes ? 'Gerando…' : `Gerar orçamento de ${mesesAntes(vigenciaMes, -1)} (leva a sobra do envelope)`}
          </button>
        </>
      )}
    </div>
  )
}
