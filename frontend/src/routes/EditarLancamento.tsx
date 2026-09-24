import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import '../components/forms.css'
import { ApiError, apiFetch } from '../lib/api'
import { ESTRUTURAS, MEIOS_PAGAMENTO, rotuloTipoMovimento } from '../lib/rotulos'
import type { Caixinha, Categoria, Conta, EstruturaCusto, MeioPagamento, Subcategoria, Transacao } from '../lib/types'

type TipoDerivado = 'receita' | 'despesa' | 'investimento' | 'reserva' | 'ajuste'

function derivarTipo(t: Transacao): TipoDerivado {
  if (t.tipo_movimento === 'receita') return 'receita'
  if (t.tipo_movimento === 'despesa') return 'despesa'
  if (t.tipo_movimento === 'estorno' || t.tipo_movimento === 'ressarcimento') return 'ajuste'
  return t.caixinha_id ? 'reserva' : 'investimento'
}

export function EditarLancamento() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [transacaoOriginal, setTransacaoOriginal] = useState<Transacao | null>(null)
  const [contas, setContas] = useState<Conta[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [despesaOriginal, setDespesaOriginal] = useState<Transacao | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erroCarga, setErroCarga] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    Promise.all([
      apiFetch<Transacao>(`/transacoes/${id}`),
      apiFetch<Conta[]>('/contas'),
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Caixinha[]>('/caixinhas'),
    ])
      .then(([t, c, cat, sub, cx]) => {
        setTransacaoOriginal(t)
        setContas(c.filter((x) => x.ativo || x.id === t.conta_id))
        setCategorias(cat.filter((x) => x.ativo || x.id === t.categoria_id))
        setSubcategorias(sub.filter((x) => x.ativo || x.id === t.subcategoria_id))
        setCaixinhas(cx.filter((x) => x.ativo || x.id === t.caixinha_id))
        setDataCompra(t.data_compra)
        setValor(String(t.valor))
        setDescricao(t.descricao ?? '')
        setContaId(t.conta_id)
        setCategoriaId(t.categoria_id ?? '')
        setSubcategoriaId(t.subcategoria_id ?? '')
        setEstruturaCusto(t.estrutura_custo ?? '')
        setCaixinhaId(t.caixinha_id ?? '')
        setMeioPagamento(t.meio_pagamento ?? '')
        if (t.ajuste_de_transacao_id) {
          apiFetch<Transacao>(`/transacoes/${t.ajuste_de_transacao_id}`)
            .then(setDespesaOriginal)
            .catch(() => {})
        }
      })
      .catch((e) => setErroCarga(e instanceof ApiError ? e.message : 'Falha ao carregar o lançamento'))
      .finally(() => setCarregando(false))
  }, [id])

  const [dataCompra, setDataCompra] = useState('')
  const [valor, setValor] = useState('')
  const [descricao, setDescricao] = useState('')
  const [contaId, setContaId] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [subcategoriaId, setSubcategoriaId] = useState('')
  const [estruturaCusto, setEstruturaCusto] = useState<EstruturaCusto | ''>('')
  const [caixinhaId, setCaixinhaId] = useState('')
  const [meioPagamento, setMeioPagamento] = useState<MeioPagamento | ''>('')

  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const tipo = transacaoOriginal ? derivarTipo(transacaoOriginal) : null

  const categoriasElegiveis = useMemo(() => {
    if (!tipo) return []
    const tipoCategoria = tipo === 'ajuste' ? 'despesa' : tipo
    if (tipoCategoria !== 'despesa' && tipoCategoria !== 'receita' && tipoCategoria !== 'investimento') return []
    return categorias.filter((c) => c.tipo === tipoCategoria)
  }, [categorias, tipo])

  const subcategoriasDaCategoria = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === categoriaId),
    [subcategorias, categoriaId],
  )

  const contaSelecionada = useMemo(() => contas.find((c) => c.id === contaId), [contas, contaId])
  const caixinhaSelecionada = useMemo(() => caixinhas.find((c) => c.id === caixinhaId), [caixinhas, caixinhaId])

  // mesmos travamentos automáticos do Novo Lançamento: despesa em conta de
  // cartão só pode ter sido paga no cartão; caixinha vinculada a uma conta
  // trava o lançamento nessa conta
  useEffect(() => {
    if (tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito') {
      setMeioPagamento('cartao_credito')
    }
  }, [tipo, contaSelecionada])

  useEffect(() => {
    if (tipo === 'reserva' && caixinhaSelecionada?.conta_id) {
      setContaId(caixinhaSelecionada.conta_id)
    }
  }, [tipo, caixinhaSelecionada])

  function selecionarSubcategoria(subId: string) {
    setSubcategoriaId(subId)
    if (tipo === 'despesa' || tipo === 'ajuste') {
      const sub = subcategorias.find((s) => s.id === subId)
      if (sub?.estrutura_custo_padrao) {
        setEstruturaCusto(sub.estrutura_custo_padrao)
      }
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    if (!transacaoOriginal || !tipo) return

    if (!contaId) {
      setErro('Escolha uma conta.')
      return
    }
    if (tipo === 'reserva' && !caixinhaId) {
      setErro('Escolha uma caixinha.')
      return
    }
    if (tipo === 'despesa' && !categoriaId) {
      setErro('Escolha uma categoria.')
      return
    }
    if (tipo === 'despesa' && !estruturaCusto) {
      setErro('Escolha uma estrutura de custo.')
      return
    }
    if (tipo === 'despesa' && !meioPagamento) {
      setErro('Escolha um meio de pagamento.')
      return
    }

    setEnviando(true)
    try {
      await apiFetch(`/transacoes/${transacaoOriginal.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          data_compra: dataCompra,
          valor: Number(valor),
          descricao: descricao || null,
          tipo_movimento: transacaoOriginal.tipo_movimento,
          conta_id: contaId,
          categoria_id: categoriaId || null,
          subcategoria_id: subcategoriaId || null,
          estrutura_custo: estruturaCusto || null,
          caixinha_id: tipo === 'reserva' ? caixinhaId : null,
          meio_pagamento: tipo === 'despesa' || tipo === 'ajuste' ? meioPagamento || null : null,
          ajuste_de_transacao_id: transacaoOriginal.ajuste_de_transacao_id,
        }),
      })
      navigate('/lancamentos')
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar o lançamento.')
    } finally {
      setEnviando(false)
    }
  }

  async function handleSubmitParcela(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    if (!transacaoOriginal) return

    if (!descricao.trim()) {
      setErro('Preencha a descrição.')
      return
    }
    if (!valor || Number(valor) <= 0) {
      setErro('Informe um valor maior que zero.')
      return
    }
    if (!categoriaId) {
      setErro('Escolha uma categoria.')
      return
    }
    if (!estruturaCusto) {
      setErro('Escolha uma estrutura de custo.')
      return
    }
    if (!meioPagamento) {
      setErro('Escolha um meio de pagamento.')
      return
    }

    setEnviando(true)
    try {
      await apiFetch(`/transacoes/parceladas/${transacaoOriginal.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          descricao,
          valor: Number(valor),
          categoria_id: categoriaId || null,
          subcategoria_id: subcategoriaId || null,
          estrutura_custo: estruturaCusto || null,
          meio_pagamento: meioPagamento || null,
        }),
      })
      navigate('/lancamentos')
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar a parcela.')
    } finally {
      setEnviando(false)
    }
  }

  if (carregando) {
    return <p>Carregando…</p>
  }

  if (erroCarga) {
    return <p className="mensagem-erro">{erroCarga}</p>
  }

  if (!transacaoOriginal || !tipo) {
    return <p className="mensagem-erro">Lançamento não encontrado.</p>
  }

  if (transacaoOriginal.pagamento === 'parcelado') {
    return (
      <div>
        <h1 style={{ fontSize: 22, marginTop: 0 }}>Editar Parcela</h1>
        <p style={{ color: 'var(--cor-texto-suave)', marginTop: -8 }}>
          Parcela {transacaoOriginal.parcela_atual}/{transacaoOriginal.parcela_total} — data e conta não são
          editáveis por aqui. Valor pode ser ajustado pra bater com a fatura real do cartão (o app não segue
          nenhum padrão bancário fixo de arredondamento entre parcelas). Pra cancelar a compra inteira, exclua a
          compra parcelada em Lançamentos e lance de novo.
        </p>

        <form className="form" onSubmit={handleSubmitParcela}>
          <div className="campo-linha">
            <label className="campo">
              Valor
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={valor}
                onChange={(e) => setValor(e.target.value)}
              />
            </label>
            <label className="campo">
              Descrição
              <input type="text" required value={descricao} onChange={(e) => setDescricao(e.target.value)} />
            </label>
          </div>

          <div className="campo-linha">
            <label className="campo">
              Categoria
              <select
                value={categoriaId}
                onChange={(e) => {
                  setCategoriaId(e.target.value)
                  setSubcategoriaId('')
                }}
                required
              >
                <option value="">Selecione…</option>
                {categoriasElegiveis.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="campo">
              Subcategoria
              <select value={subcategoriaId} onChange={(e) => selecionarSubcategoria(e.target.value)} disabled={!categoriaId}>
                <option value="">Nenhuma</option>
                {subcategoriasDaCategoria.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="campo-linha">
            <label className="campo">
              Estrutura de custo
              <select
                value={estruturaCusto}
                onChange={(e) => setEstruturaCusto(e.target.value as EstruturaCusto | '')}
                required
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
                value={meioPagamento}
                onChange={(e) => setMeioPagamento(e.target.value as MeioPagamento | '')}
                disabled={contaSelecionada?.tipo_conta === 'cartao_credito'}
                required
              >
                <option value="">Selecione…</option>
                {MEIOS_PAGAMENTO.map((m) => (
                  <option key={m.valor} value={m.valor}>
                    {m.rotulo}
                  </option>
                ))}
              </select>
              {contaSelecionada?.tipo_conta === 'cartao_credito' && (
                <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
                  Fixo em Cartão de crédito — a conta desta parcela é um cartão.
                </span>
              )}
            </label>
          </div>

          {erro && (
            <p role="alert" className="mensagem-erro">
              {erro}
            </p>
          )}

          <div className="form-acoes">
            <button type="submit" className="botao-primario" disabled={enviando}>
              {enviando ? 'Salvando…' : 'Salvar alterações'}
            </button>
            <Link to="/lancamentos" className="botao-secundario">
              Cancelar
            </Link>
          </div>
        </form>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Editar Lançamento</h1>
      <p style={{ color: 'var(--cor-texto-suave)', marginTop: -8 }}>
        Tipo: {rotuloTipoMovimento(transacaoOriginal.tipo_movimento)}
        {tipo === 'reserva' ? ' (Reserva)' : ''}
        {tipo === 'investimento' ? ' (Investimento)' : ''}
        {' — não é possível trocar o tipo por aqui; exclua e lance novamente se precisar.'}
      </p>

      <form className="form" onSubmit={handleSubmit}>
        {tipo === 'ajuste' && despesaOriginal && (
          <div className="campo">
            <span>Despesa original</span>
            <div className="despesa-selecionada">
              <span>
                {despesaOriginal.data_compra} — {despesaOriginal.descricao ?? '(sem descrição)'} — R${' '}
                {despesaOriginal.valor.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        <div className="campo-linha">
          <label className="campo">
            Valor
            <input
              type="number"
              step="0.01"
              min="0"
              required
              value={valor}
              onChange={(e) => setValor(e.target.value)}
            />
          </label>
          <label className="campo">
            Data
            <input type="date" required value={dataCompra} onChange={(e) => setDataCompra(e.target.value)} />
          </label>
        </div>

        <label className="campo">
          Descrição
          <input type="text" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </label>

        <label className="campo">
          Conta
          <select
            value={contaId}
            onChange={(e) => setContaId(e.target.value)}
            required
            disabled={tipo === 'reserva' && !!caixinhaSelecionada?.conta_id}
          >
            <option value="">Selecione…</option>
            {contas.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
          {tipo === 'reserva' && caixinhaSelecionada?.conta_id && (
            <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
              Fixo na conta vinculada à caixinha "{caixinhaSelecionada.nome}".
            </span>
          )}
        </label>

        {tipo === 'reserva' && (
          <label className="campo">
            Caixinha
            <select value={caixinhaId} onChange={(e) => setCaixinhaId(e.target.value)} required>
              <option value="">Selecione…</option>
              {caixinhas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
        )}

        {tipo !== 'reserva' && (
          <div className="campo-linha">
            <label className="campo">
              Categoria
              <select
                value={categoriaId}
                onChange={(e) => {
                  setCategoriaId(e.target.value)
                  setSubcategoriaId('')
                }}
                required={tipo === 'despesa'}
              >
                <option value="">{tipo === 'despesa' ? 'Selecione…' : 'Nenhuma'}</option>
                {categoriasElegiveis.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
            <label className="campo">
              Subcategoria
              <select
                value={subcategoriaId}
                onChange={(e) => selecionarSubcategoria(e.target.value)}
                disabled={!categoriaId}
              >
                <option value="">Nenhuma</option>
                {subcategoriasDaCategoria.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}

        {(tipo === 'despesa' || tipo === 'ajuste') && (
          <div className="campo-linha">
            <label className="campo">
              Estrutura de custo
              <select
                value={estruturaCusto}
                onChange={(e) => setEstruturaCusto(e.target.value as EstruturaCusto | '')}
                required={tipo === 'despesa'}
              >
                <option value="">{tipo === 'despesa' ? 'Selecione…' : 'Nenhuma'}</option>
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
                value={meioPagamento}
                onChange={(e) => setMeioPagamento(e.target.value as MeioPagamento | '')}
                disabled={tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito'}
                required={tipo === 'despesa'}
              >
                <option value="">{tipo === 'despesa' ? 'Selecione…' : 'Nenhum'}</option>
                {MEIOS_PAGAMENTO.map((m) => (
                  <option key={m.valor} value={m.valor}>
                    {m.rotulo}
                  </option>
                ))}
              </select>
              {tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito' && (
                <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
                  Fixo em Cartão de crédito — a conta escolhida é um cartão.
                </span>
              )}
            </label>
          </div>
        )}

        {erro && (
          <p role="alert" className="mensagem-erro">
            {erro}
          </p>
        )}

        <div className="form-acoes">
          <button type="submit" className="botao-primario" disabled={enviando}>
            {enviando ? 'Salvando…' : 'Salvar alterações'}
          </button>
          <Link to="/lancamentos" className="botao-secundario">
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  )
}
