import { useEffect, useMemo, useState, type FormEvent } from 'react'
import '../../components/crud.css'
import '../../components/forms.css'
import { ApiError, apiFetch } from '../../lib/api'
import { formatarMoeda } from '../../lib/formatar'
import { rotuloMesLongo } from '../../lib/periodo'
import { ESTRUTURAS, MEIOS_PAGAMENTO } from '../../lib/rotulos'
import type {
  Categoria,
  Conta,
  EstruturaCustoRecorrente,
  LancamentoRecorrente,
  MeioPagamento,
  MesPulado,
  Subcategoria,
} from '../../lib/types'

type FormState = {
  descricao: string
  valor: string
  dia_mes: string
  conta_id: string
  categoria_id: string
  subcategoria_id: string
  estrutura_custo: EstruturaCustoRecorrente | ''
  meio_pagamento: MeioPagamento | ''
  data_inicio: string
  data_fim: string
}

function ordenarPorDescricao(lista: LancamentoRecorrente[]): LancamentoRecorrente[] {
  return [...lista].sort((a, b) => a.descricao.localeCompare(b.descricao, 'pt-BR'))
}

const FORM_VAZIO: FormState = {
  descricao: '',
  valor: '',
  dia_mes: '',
  conta_id: '',
  categoria_id: '',
  subcategoria_id: '',
  estrutura_custo: '',
  meio_pagamento: '',
  data_inicio: '',
  data_fim: '',
}

export function LancamentosRecorrentesSection() {
  const [recorrentes, setRecorrentes] = useState<LancamentoRecorrente[] | null>(null)
  const [contas, setContas] = useState<Conta[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(FORM_VAZIO)
  const [salvando, setSalvando] = useState(false)

  const [criandoCategoria, setCriandoCategoria] = useState(false)
  const [novaCategoriaNome, setNovaCategoriaNome] = useState('')
  const [salvandoCategoria, setSalvandoCategoria] = useState(false)
  const [erroCategoria, setErroCategoria] = useState<string | null>(null)

  const [criandoSubcategoria, setCriandoSubcategoria] = useState(false)
  const [novaSubcategoriaNome, setNovaSubcategoriaNome] = useState('')
  const [novaSubcategoriaEstrutura, setNovaSubcategoriaEstrutura] = useState<EstruturaCustoRecorrente | ''>('')
  const [salvandoSubcategoria, setSalvandoSubcategoria] = useState(false)
  const [erroSubcategoria, setErroSubcategoria] = useState<string | null>(null)

  // meses pulados — carregado sob demanda (só quando o usuário abre "Meses
  // pulados" de um recorrente), pra não bater 1 GET a mais por recorrente
  // já na carga inicial da tela
  const [pulados, setPulados] = useState<Record<string, MesPulado[]>>({})
  const [carregandoPulados, setCarregandoPulados] = useState<string | null>(null)
  const [desfazendoPulado, setDesfazendoPulado] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      apiFetch<LancamentoRecorrente[]>('/lancamentos-recorrentes'),
      apiFetch<Conta[]>('/contas'),
      apiFetch<Categoria[]>('/categorias?tipo=despesa'),
      apiFetch<Subcategoria[]>('/subcategorias'),
    ])
      .then(([r, c, cat, sub]) => {
        setRecorrentes(r)
        setContas(c.filter((x) => x.ativo))
        setCategorias(cat.filter((x) => x.ativo))
        setSubcategorias(sub)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar lançamentos recorrentes'))
  }, [])

  const subcategoriasDaCategoria = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === form.categoria_id && s.ativo),
    [subcategorias, form.categoria_id],
  )

  function nomeConta(id: string) {
    return contas.find((c) => c.id === id)?.nome ?? 'conta removida'
  }

  function nomeCategoria(id: string) {
    return categorias.find((c) => c.id === id)?.nome ?? 'categoria removida'
  }

  function fecharCriacaoInline() {
    setCriandoCategoria(false)
    setNovaCategoriaNome('')
    setErroCategoria(null)
    setCriandoSubcategoria(false)
    setNovaSubcategoriaNome('')
    setNovaSubcategoriaEstrutura('')
    setErroSubcategoria(null)
  }

  function iniciarCriacao() {
    setForm(FORM_VAZIO)
    setEditandoId(null)
    setMostrarForm(true)
    fecharCriacaoInline()
  }

  function iniciarEdicao(r: LancamentoRecorrente) {
    setForm({
      descricao: r.descricao,
      valor: String(r.valor),
      dia_mes: String(r.dia_mes),
      conta_id: r.conta_id,
      categoria_id: r.categoria_id,
      subcategoria_id: r.subcategoria_id ?? '',
      estrutura_custo: r.estrutura_custo,
      meio_pagamento: r.meio_pagamento,
      data_inicio: r.data_inicio,
      data_fim: r.data_fim ?? '',
    })
    setEditandoId(r.id)
    setMostrarForm(true)
    fecharCriacaoInline()
  }

  function escolherCategoria(id: string) {
    setForm((f) => ({ ...f, categoria_id: id, subcategoria_id: '' }))
    setCriandoCategoria(false)
  }

  function escolherSubcategoria(id: string) {
    // sugestão de estrutura de custo da subcategoria, mesmo padrão do
    // Novo Lançamento — não se aplica se o padrão for 'investimentos'
    // (recorrente só aceita fixo/variavel/sazonal, é sempre despesa)
    const sub = subcategorias.find((s) => s.id === id)
    const sugestao =
      sub?.estrutura_custo_padrao && sub.estrutura_custo_padrao !== 'investimentos'
        ? (sub.estrutura_custo_padrao as EstruturaCustoRecorrente)
        : null
    setForm((f) => ({ ...f, subcategoria_id: id, estrutura_custo: sugestao ?? f.estrutura_custo }))
  }

  async function criarCategoria() {
    const nome = novaCategoriaNome.trim()
    if (!nome) return
    setSalvandoCategoria(true)
    setErroCategoria(null)
    try {
      const nova = await apiFetch<Categoria>('/categorias', {
        method: 'POST',
        body: JSON.stringify({ nome, tipo: 'despesa' }),
      })
      setCategorias((prev) => [...prev, nova].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')))
      escolherCategoria(nova.id)
      setNovaCategoriaNome('')
    } catch (e) {
      setErroCategoria(e instanceof ApiError ? e.message : 'Falha ao criar categoria.')
    } finally {
      setSalvandoCategoria(false)
    }
  }

  async function criarSubcategoria() {
    const nome = novaSubcategoriaNome.trim()
    if (!nome || !form.categoria_id) return
    setSalvandoSubcategoria(true)
    setErroSubcategoria(null)
    try {
      const nova = await apiFetch<Subcategoria>('/subcategorias', {
        method: 'POST',
        body: JSON.stringify({
          nome,
          categoria_id: form.categoria_id,
          estrutura_custo_padrao: novaSubcategoriaEstrutura || null,
        }),
      })
      setSubcategorias((prev) => [...prev, nova].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')))
      setForm((f) => ({ ...f, subcategoria_id: nova.id }))
      setNovaSubcategoriaNome('')
      setNovaSubcategoriaEstrutura('')
      setCriandoSubcategoria(false)
    } catch (e) {
      setErroSubcategoria(e instanceof ApiError ? e.message : 'Falha ao criar subcategoria.')
    } finally {
      setSalvandoSubcategoria(false)
    }
  }

  async function toggleAtivo(r: LancamentoRecorrente) {
    const atualizado = await apiFetch<LancamentoRecorrente>(
      `/lancamentos-recorrentes/${r.id}/ativo?ativo=${!r.ativo}`,
      { method: 'PATCH' },
    )
    setRecorrentes((atual) => atual!.map((x) => (x.id === atualizado.id ? atualizado : x)))
  }

  async function excluir(r: LancamentoRecorrente) {
    if (!window.confirm(`Apagar "${r.descricao}"? Meses já confirmados continuam existindo como lançamentos normais.`))
      return
    await apiFetch(`/lancamentos-recorrentes/${r.id}`, { method: 'DELETE' })
    setRecorrentes((atual) => atual!.filter((x) => x.id !== r.id))
  }

  async function toggleMesesPulados(recorrenteId: string) {
    if (pulados[recorrenteId]) {
      setPulados((atual) => {
        const restante = { ...atual }
        delete restante[recorrenteId]
        return restante
      })
      return
    }
    setErro(null)
    setCarregandoPulados(recorrenteId)
    try {
      const lista = await apiFetch<MesPulado[]>(`/lancamentos-recorrentes/${recorrenteId}/pulados`)
      setPulados((atual) => ({ ...atual, [recorrenteId]: lista }))
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : 'Falha ao carregar meses pulados')
    } finally {
      setCarregandoPulados(null)
    }
  }

  async function desfazerPulado(recorrenteId: string, vigenciaMes: string) {
    const chave = `${recorrenteId}:${vigenciaMes}`
    setErro(null)
    setDesfazendoPulado(chave)
    try {
      await apiFetch(`/lancamentos-recorrentes/${recorrenteId}/pular?vigencia_mes=${vigenciaMes}`, {
        method: 'DELETE',
      })
      setPulados((atual) => ({
        ...atual,
        [recorrenteId]: (atual[recorrenteId] ?? []).filter((p) => p.vigencia_mes !== vigenciaMes),
      }))
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : 'Falha ao desfazer o pular')
    } finally {
      setDesfazendoPulado(null)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      const payload = {
        descricao: form.descricao,
        valor: Number(form.valor),
        dia_mes: Number(form.dia_mes),
        conta_id: form.conta_id,
        categoria_id: form.categoria_id,
        subcategoria_id: form.subcategoria_id || null,
        estrutura_custo: form.estrutura_custo,
        meio_pagamento: form.meio_pagamento,
        data_inicio: form.data_inicio,
        data_fim: form.data_fim || null,
      }
      if (editandoId) {
        const atualizado = await apiFetch<LancamentoRecorrente>(`/lancamentos-recorrentes/${editandoId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        setRecorrentes((atual) => ordenarPorDescricao(atual!.map((x) => (x.id === atualizado.id ? atualizado : x))))
      } else {
        const criado = await apiFetch<LancamentoRecorrente>('/lancamentos-recorrentes', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setRecorrentes((atual) => ordenarPorDescricao([...(atual ?? []), criado]))
      }
      setMostrarForm(false)
    } catch (e) {
      setErro(
        e instanceof ApiError
          ? typeof e.detail === 'string'
            ? e.detail
            : e.message
          : 'Falha ao salvar lançamento recorrente',
      )
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div>
      <div className="secao-cabecalho">
        <h2>Despesas Fixas Recorrentes</h2>
        {!mostrarForm && (
          <button type="button" className="botao-primario" onClick={iniciarCriacao}>
            + Novo recorrente
          </button>
        )}
      </div>

      <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13, marginTop: -4 }}>
        Aluguel, assinaturas — cadastradas aqui só viram lançamento de verdade quando você confirmar o mês em
        "Compromissos Futuros" no Dashboard.
      </p>

      {erro && <p className="mensagem-erro">{erro}</p>}

      {mostrarForm && (
        <form className="form" onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
          <div className="campo-linha">
            <label className="campo">
              Descrição
              <input
                type="text"
                required
                value={form.descricao}
                onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              />
            </label>
            <label className="campo" style={{ maxWidth: 140 }}>
              Valor
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={form.valor}
                onChange={(e) => setForm({ ...form, valor: e.target.value })}
              />
            </label>
            <label className="campo" style={{ maxWidth: 120 }}>
              Dia do mês
              <input
                type="number"
                min="1"
                max="31"
                required
                value={form.dia_mes}
                onChange={(e) => setForm({ ...form, dia_mes: e.target.value })}
              />
            </label>
          </div>

          <div className="campo-linha">
            <label className="campo">
              Conta
              <select
                required
                value={form.conta_id}
                onChange={(e) => setForm({ ...form, conta_id: e.target.value })}
              >
                <option value="">Selecione…</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="campo">
              Categoria
              <select required value={form.categoria_id} onChange={(e) => escolherCategoria(e.target.value)}>
                <option value="">Selecione…</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="chip chip-criar chip-solta"
                onClick={() => setCriandoCategoria((v) => !v)}
              >
                + Nova categoria
              </button>
              {criandoCategoria && (
                <div className="chip-form">
                  <input
                    type="text"
                    placeholder="Nome da categoria de despesa"
                    value={novaCategoriaNome}
                    onChange={(e) => setNovaCategoriaNome(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        criarCategoria()
                      }
                    }}
                    autoFocus
                  />
                  <button
                    type="button"
                    className="botao-secundario"
                    disabled={salvandoCategoria || !novaCategoriaNome.trim()}
                    onClick={criarCategoria}
                  >
                    {salvandoCategoria ? 'Criando…' : 'Criar'}
                  </button>
                  <button
                    type="button"
                    className="chip-cancelar"
                    onClick={() => {
                      setCriandoCategoria(false)
                      setNovaCategoriaNome('')
                      setErroCategoria(null)
                    }}
                  >
                    Cancelar
                  </button>
                  {erroCategoria && <p className="mensagem-erro">{erroCategoria}</p>}
                </div>
              )}
            </label>
            <label className="campo">
              Subcategoria
              <select
                value={form.subcategoria_id}
                onChange={(e) => escolherSubcategoria(e.target.value)}
                disabled={!form.categoria_id}
              >
                <option value="">Nenhuma</option>
                {subcategoriasDaCategoria.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
              {form.categoria_id && (
                <button
                  type="button"
                  className="chip chip-criar chip-solta"
                  onClick={() => setCriandoSubcategoria((v) => !v)}
                >
                  + Nova subcategoria
                </button>
              )}
              {criandoSubcategoria && (
                <div className="chip-form">
                  <input
                    type="text"
                    placeholder="Nome da subcategoria"
                    value={novaSubcategoriaNome}
                    onChange={(e) => setNovaSubcategoriaNome(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        criarSubcategoria()
                      }
                    }}
                    autoFocus
                  />
                  <select
                    value={novaSubcategoriaEstrutura}
                    onChange={(e) => setNovaSubcategoriaEstrutura(e.target.value as EstruturaCustoRecorrente | '')}
                    title="Estrutura de custo padrão — sugerida sozinha nos próximos recorrentes com essa subcategoria"
                  >
                    <option value="">Estrutura padrão (opcional)</option>
                    {ESTRUTURAS.filter((e) => e.valor !== 'investimentos').map((e) => (
                      <option key={e.valor} value={e.valor}>
                        {e.rotulo}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="botao-secundario"
                    disabled={salvandoSubcategoria || !novaSubcategoriaNome.trim()}
                    onClick={criarSubcategoria}
                  >
                    {salvandoSubcategoria ? 'Criando…' : 'Criar'}
                  </button>
                  <button
                    type="button"
                    className="chip-cancelar"
                    onClick={() => {
                      setCriandoSubcategoria(false)
                      setNovaSubcategoriaNome('')
                      setNovaSubcategoriaEstrutura('')
                      setErroSubcategoria(null)
                    }}
                  >
                    Cancelar
                  </button>
                  {erroSubcategoria && <p className="mensagem-erro">{erroSubcategoria}</p>}
                </div>
              )}
            </label>
          </div>

          <div className="campo-linha">
            <label className="campo">
              Estrutura de custo
              <select
                required
                value={form.estrutura_custo}
                onChange={(e) => setForm({ ...form, estrutura_custo: e.target.value as EstruturaCustoRecorrente })}
              >
                <option value="">Selecione…</option>
                {ESTRUTURAS.filter((e) => e.valor !== 'investimentos').map((e) => (
                  <option key={e.valor} value={e.valor}>
                    {e.rotulo}
                  </option>
                ))}
              </select>
            </label>
            <label className="campo">
              Meio de pagamento
              <select
                required
                value={form.meio_pagamento}
                onChange={(e) => setForm({ ...form, meio_pagamento: e.target.value as MeioPagamento })}
              >
                <option value="">Selecione…</option>
                {MEIOS_PAGAMENTO.map((m) => (
                  <option key={m.valor} value={m.valor}>
                    {m.rotulo}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="campo-linha">
            <label className="campo">
              Início
              <input
                type="date"
                required
                value={form.data_inicio}
                onChange={(e) => setForm({ ...form, data_inicio: e.target.value })}
              />
            </label>
            <label className="campo">
              Fim (opcional)
              <input
                type="date"
                value={form.data_fim}
                onChange={(e) => setForm({ ...form, data_fim: e.target.value })}
              />
            </label>
          </div>

          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={salvando}>
              {salvando ? 'Salvando…' : editandoId ? 'Salvar alterações' : 'Criar recorrente'}
            </button>
            <button
              type="button"
              className="botao-secundario"
              onClick={() => {
                setMostrarForm(false)
                fecharCriacaoInline()
              }}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {recorrentes === null && <p>Carregando…</p>}
      {recorrentes?.length === 0 && <p>Nenhuma despesa fixa recorrente cadastrada ainda.</p>}
      {recorrentes && recorrentes.length > 0 && (
        <ul className="lista-crud">
          {recorrentes.map((r) => (
            <li key={r.id} className={r.ativo ? '' : 'item-inativo'}>
              <div className="item-linha">
                <div className="item-info">
                  <span className="item-titulo">{r.descricao}</span>
                  <span className="item-detalhe">
                    {formatarMoeda(r.valor)} · dia {r.dia_mes} · {nomeCategoria(r.categoria_id)} · {nomeConta(r.conta_id)}
                    {!r.ativo && ' — inativo'}
                  </span>
                </div>
                <div className="item-acoes">
                  <button type="button" className="botao-link" onClick={() => iniciarEdicao(r)}>
                    Editar
                  </button>
                  <button type="button" className="botao-link" onClick={() => toggleAtivo(r)}>
                    {r.ativo ? 'Desativar' : 'Reativar'}
                  </button>
                  <button type="button" className="botao-link" onClick={() => toggleMesesPulados(r.id)}>
                    {carregandoPulados === r.id
                      ? 'Carregando…'
                      : pulados[r.id]
                        ? 'Ocultar meses pulados'
                        : 'Meses pulados'}
                  </button>
                  <button type="button" className="botao-link" onClick={() => excluir(r)}>
                    Excluir
                  </button>
                </div>
              </div>
              {pulados[r.id] && (
                <div className="chip-form" style={{ marginTop: 8 }}>
                  {pulados[r.id].length === 0 ? (
                    <p style={{ color: 'var(--cor-texto-suave)', fontSize: 13, margin: 0 }}>
                      Nenhum mês pulado pra este recorrente.
                    </p>
                  ) : (
                    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {pulados[r.id].map((p) => {
                        const chave = `${r.id}:${p.vigencia_mes}`
                        return (
                          <li key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
                            <span>{rotuloMesLongo(p.vigencia_mes.slice(0, 7))}</span>
                            <button
                              type="button"
                              className="botao-link"
                              disabled={desfazendoPulado === chave}
                              onClick={() => desfazerPulado(r.id, p.vigencia_mes)}
                            >
                              {desfazendoPulado === chave ? 'Desfazendo…' : 'Desfazer'}
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
