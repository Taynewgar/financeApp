import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import '../components/forms.css'
import { ApiError, apiFetch } from '../lib/api'
import type {
  Caixinha,
  Categoria,
  Conta,
  EstruturaCusto,
  MeioPagamento,
  Subcategoria,
  Transacao,
  TipoMovimento,
} from '../lib/types'

type TipoSelecionado = 'receita' | 'despesa' | 'investimento' | 'reserva' | 'ajuste'
type Direcao = 'aplicacao' | 'retirada'

const TIPOS: { valor: TipoSelecionado; rotulo: string }[] = [
  { valor: 'despesa', rotulo: 'Despesa' },
  { valor: 'receita', rotulo: 'Receita' },
  { valor: 'investimento', rotulo: 'Investimento' },
  { valor: 'reserva', rotulo: 'Reserva' },
  { valor: 'ajuste', rotulo: 'Estorno/Ressarcimento' },
]

const ESTRUTURAS: { valor: EstruturaCusto; rotulo: string }[] = [
  { valor: 'fixo', rotulo: 'Fixo' },
  { valor: 'variavel', rotulo: 'Variável' },
  { valor: 'sazonal', rotulo: 'Sazonal' },
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

function hoje() {
  return new Date().toISOString().slice(0, 10)
}

export function NovoLancamento() {
  const [contas, setContas] = useState<Conta[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [subcategorias, setSubcategorias] = useState<Subcategoria[]>([])
  const [caixinhas, setCaixinhas] = useState<Caixinha[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erroCarga, setErroCarga] = useState<string | null>(null)

  // só o essencial pra montar a tela — a busca da despesa original (usada
  // só no Estorno/Ressarcimento) é feita sob demanda, não aqui, pra não
  // pesar a abertura do formulário com o histórico inteiro de despesas
  useEffect(() => {
    Promise.all([
      apiFetch<Conta[]>('/contas'),
      apiFetch<Categoria[]>('/categorias'),
      apiFetch<Subcategoria[]>('/subcategorias'),
      apiFetch<Caixinha[]>('/caixinhas'),
    ])
      .then(([c, cat, sub, cx]) => {
        setContas(c.filter((x) => x.ativo))
        setCategorias(cat.filter((x) => x.ativo))
        setSubcategorias(sub.filter((x) => x.ativo))
        setCaixinhas(cx.filter((x) => x.ativo))
      })
      .catch((e) => setErroCarga(e instanceof ApiError ? e.message : 'Falha ao carregar dados do formulário'))
      .finally(() => setCarregando(false))
  }, [])

  const [tipo, setTipo] = useState<TipoSelecionado>('despesa')
  const [ajusteTipo, setAjusteTipo] = useState<'estorno' | 'ressarcimento'>('estorno')
  const [direcao, setDirecao] = useState<Direcao>('aplicacao')
  const [pagamento, setPagamento] = useState<'avista' | 'parcelado'>('avista')

  const [dataCompra, setDataCompra] = useState(hoje())
  const [valor, setValor] = useState('')
  const [descricao, setDescricao] = useState('')
  const [contaId, setContaId] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [subcategoriaId, setSubcategoriaId] = useState('')
  const [estruturaCusto, setEstruturaCusto] = useState<EstruturaCusto | ''>('')
  const [caixinhaId, setCaixinhaId] = useState('')
  const [meioPagamento, setMeioPagamento] = useState<MeioPagamento | ''>('')

  const [valorTotal, setValorTotal] = useState('')
  const [parcelaTotal, setParcelaTotal] = useState('2')
  const [dataPrimeiraParcela, setDataPrimeiraParcela] = useState(hoje())

  // busca da despesa original do estorno/ressarcimento: sob demanda e
  // filtrada no backend, em vez de um <select> com todo o histórico
  const [buscaDespesa, setBuscaDespesa] = useState('')
  const [buscandoDespesa, setBuscandoDespesa] = useState(false)
  const [resultadosDespesa, setResultadosDespesa] = useState<Transacao[]>([])
  const [despesaSelecionada, setDespesaSelecionada] = useState<Transacao | null>(null)

  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState(false)

  // categoria é escolhida entre as do tipo compatível (receita/despesa/
  // investimento) — igual pra qualquer tipo de lançamento, sem parentesco
  // fixo (ver regra em backend/app/schemas/categorias.py)
  const categoriasElegiveis = useMemo(() => {
    const tipoCategoria = tipo === 'ajuste' ? 'despesa' : tipo
    if (tipoCategoria !== 'despesa' && tipoCategoria !== 'receita' && tipoCategoria !== 'investimento') return []
    return categorias.filter((c) => c.tipo === tipoCategoria)
  }, [categorias, tipo])

  const rotuloTipoCategoria =
    tipo === 'receita' ? 'Receita' : tipo === 'investimento' ? 'Investimento' : 'Despesa'

  const subcategoriasDaCategoria = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === categoriaId),
    [subcategorias, categoriaId],
  )

  const contaSelecionada = useMemo(() => contas.find((c) => c.id === contaId), [contas, contaId])

  // ao trocar o tipo, a categoria elegível muda — limpa a escolha anterior;
  // investimento tem estrutura de custo fixa, independente da categoria
  useEffect(() => {
    setCategoriaId('')
    setSubcategoriaId('')
    setEstruturaCusto(tipo === 'investimento' ? 'investimentos' : '')
  }, [tipo])

  // despesa numa conta de cartão de crédito só pode ter sido paga no
  // cartão — trava o campo em vez de deixar escolher outra coisa
  useEffect(() => {
    if (tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito') {
      setMeioPagamento('cartao_credito')
    }
  }, [tipo, contaSelecionada])

  // debounce simples: espera parar de digitar antes de consultar a API
  useEffect(() => {
    if (tipo !== 'ajuste' || despesaSelecionada) return
    if (!buscaDespesa.trim()) {
      setResultadosDespesa([])
      return
    }
    setBuscandoDespesa(true)
    const timer = setTimeout(() => {
      apiFetch<Transacao[]>(`/transacoes?tipo_movimento=despesa&descricao=${encodeURIComponent(buscaDespesa.trim())}`)
        .then((res) => setResultadosDespesa(res.slice(0, 20)))
        .catch(() => setResultadosDespesa([]))
        .finally(() => setBuscandoDespesa(false))
    }, 350)
    return () => clearTimeout(timer)
  }, [buscaDespesa, tipo, despesaSelecionada])

  function selecionarSubcategoria(id: string) {
    setSubcategoriaId(id)
    // a sugestão de estrutura de custo da subcategoria só se aplica quando
    // a estrutura é livre (despesa/ajuste) — investimento já é fixa
    if (tipo === 'despesa' || tipo === 'ajuste') {
      const sub = subcategorias.find((s) => s.id === id)
      if (sub?.estrutura_custo_padrao) {
        setEstruturaCusto(sub.estrutura_custo_padrao)
      }
    }
  }

  function selecionarDespesaOriginal(d: Transacao) {
    setDespesaSelecionada(d)
    setContaId(d.conta_id)
    setCategoriaId(d.categoria_id ?? '')
    setSubcategoriaId(d.subcategoria_id ?? '')
    setEstruturaCusto(d.estrutura_custo ?? '')
  }

  function trocarDespesaOriginal() {
    setDespesaSelecionada(null)
    setBuscaDespesa('')
    setResultadosDespesa([])
  }

  function resetarFormulario() {
    setTipo('despesa')
    setAjusteTipo('estorno')
    setDirecao('aplicacao')
    setPagamento('avista')
    setDataCompra(hoje())
    setValor('')
    setDescricao('')
    setContaId('')
    setCategoriaId('')
    setSubcategoriaId('')
    setEstruturaCusto('')
    setCaixinhaId('')
    setMeioPagamento('')
    setValorTotal('')
    setParcelaTotal('2')
    setDataPrimeiraParcela(hoje())
    trocarDespesaOriginal()
    setSucesso(false)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setErro(null)

    if (!contaId) {
      setErro('Escolha uma conta.')
      return
    }
    if (tipo === 'ajuste' && !despesaSelecionada) {
      setErro('Escolha a despesa original que está sendo estornada/ressarcida.')
      return
    }
    if (tipo === 'reserva' && !caixinhaId) {
      setErro('Escolha uma caixinha.')
      return
    }
    if ((tipo === 'receita' || tipo === 'investimento') && categoriasElegiveis.length === 0) {
      setErro(`Crie uma categoria do tipo ${rotuloTipoCategoria} em Configurações antes de lançar.`)
      return
    }

    setEnviando(true)
    try {
      if (tipo === 'despesa' && pagamento === 'parcelado') {
        if (!descricao.trim()) {
          throw new ApiError(422, 'Descrição é obrigatória em compra parcelada.')
        }
        await apiFetch('/transacoes/parceladas', {
          method: 'POST',
          body: JSON.stringify({
            descricao,
            valor_total: Number(valorTotal),
            parcela_total: Number(parcelaTotal),
            data_primeira_parcela: dataPrimeiraParcela,
            conta_id: contaId,
            categoria_id: categoriaId || null,
            subcategoria_id: subcategoriaId || null,
            estrutura_custo: estruturaCusto || null,
            meio_pagamento: meioPagamento || null,
          }),
        })
      } else {
        const tipoMovimento: TipoMovimento =
          tipo === 'ajuste' ? ajusteTipo : tipo === 'investimento' || tipo === 'reserva' ? direcao : tipo

        await apiFetch('/transacoes', {
          method: 'POST',
          body: JSON.stringify({
            data_compra: dataCompra,
            valor: Number(valor),
            descricao: descricao || null,
            tipo_movimento: tipoMovimento,
            conta_id: contaId,
            categoria_id: categoriaId || null,
            subcategoria_id: subcategoriaId || null,
            estrutura_custo: estruturaCusto || null,
            caixinha_id: tipo === 'reserva' ? caixinhaId : null,
            meio_pagamento: tipo === 'despesa' || tipo === 'ajuste' ? meioPagamento || null : null,
            ajuste_de_transacao_id: tipo === 'ajuste' ? despesaSelecionada!.id : null,
          }),
        })
      }
      setSucesso(true)
    } catch (e) {
      if (e instanceof ApiError) {
        setErro(typeof e.detail === 'string' ? e.detail : e.message)
      } else {
        setErro('Falha ao salvar o lançamento.')
      }
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

  if (sucesso) {
    return (
      <div>
        <h1 style={{ fontSize: 22, marginTop: 0 }}>Lançamento salvo</h1>
        <p className="mensagem-sucesso">Tudo certo — o lançamento foi registrado.</p>
        <div className="form-acoes">
          <button type="button" className="botao-primario" onClick={resetarFormulario}>
            Lançar outro
          </button>
          <Link to="/dashboard" className="botao-secundario">
            Ver Dashboard
          </Link>
        </div>
      </div>
    )
  }

  if (contas.length === 0) {
    return (
      <div>
        <h1 style={{ fontSize: 22, marginTop: 0 }}>Novo Lançamento</h1>
        <p>
          Você ainda não tem nenhuma conta cadastrada. Crie uma conta em Configurações antes de lançar uma
          transação.
        </p>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Novo Lançamento</h1>

      <form className="form" onSubmit={handleSubmit}>
        <div className="campo">
          <span>Tipo</span>
          <div className="segmentado">
            {TIPOS.map((t) => (
              <button
                key={t.valor}
                type="button"
                className={tipo === t.valor ? 'ativo' : ''}
                onClick={() => setTipo(t.valor)}
              >
                {t.rotulo}
              </button>
            ))}
          </div>
        </div>

        {tipo === 'ajuste' && (
          <div className="campo">
            <span>É um</span>
            <div className="segmentado">
              <button
                type="button"
                className={ajusteTipo === 'estorno' ? 'ativo' : ''}
                onClick={() => setAjusteTipo('estorno')}
              >
                Estorno
              </button>
              <button
                type="button"
                className={ajusteTipo === 'ressarcimento' ? 'ativo' : ''}
                onClick={() => setAjusteTipo('ressarcimento')}
              >
                Ressarcimento
              </button>
            </div>
          </div>
        )}

        {(tipo === 'investimento' || tipo === 'reserva') && (
          <div className="campo">
            <span>Direção</span>
            <div className="segmentado">
              <button type="button" className={direcao === 'aplicacao' ? 'ativo' : ''} onClick={() => setDirecao('aplicacao')}>
                Aplicação
              </button>
              <button type="button" className={direcao === 'retirada' ? 'ativo' : ''} onClick={() => setDirecao('retirada')}>
                Retirada
              </button>
            </div>
          </div>
        )}

        {tipo === 'ajuste' && (
          <div className="campo">
            <span>Despesa original</span>
            {despesaSelecionada ? (
              <div className="despesa-selecionada">
                <span>
                  {despesaSelecionada.data_compra} — {despesaSelecionada.descricao ?? '(sem descrição)'} — R${' '}
                  {despesaSelecionada.valor.toFixed(2)}
                </span>
                <button type="button" className="botao-secundario" onClick={trocarDespesaOriginal}>
                  Trocar
                </button>
              </div>
            ) : (
              <>
                <input
                  type="text"
                  placeholder="Buscar pela descrição da despesa…"
                  value={buscaDespesa}
                  onChange={(e) => setBuscaDespesa(e.target.value)}
                />
                {buscandoDespesa && <p>Buscando…</p>}
                {resultadosDespesa.length > 0 && (
                  <ul className="busca-resultados">
                    {resultadosDespesa.map((d) => (
                      <li key={d.id}>
                        <button type="button" onClick={() => selecionarDespesaOriginal(d)}>
                          {d.data_compra} — {d.descricao ?? '(sem descrição)'} — R$ {d.valor.toFixed(2)}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        )}

        {tipo === 'despesa' && (
          <div className="campo">
            <span>Pagamento</span>
            <div className="segmentado">
              <button
                type="button"
                className={pagamento === 'avista' ? 'ativo' : ''}
                onClick={() => setPagamento('avista')}
              >
                À vista
              </button>
              <button
                type="button"
                className={pagamento === 'parcelado' ? 'ativo' : ''}
                onClick={() => setPagamento('parcelado')}
              >
                Parcelado
              </button>
            </div>
          </div>
        )}

        {tipo === 'despesa' && pagamento === 'parcelado' ? (
          <div className="campo-linha">
            <label className="campo">
              Valor total
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={valorTotal}
                onChange={(e) => setValorTotal(e.target.value)}
              />
            </label>
            <label className="campo">
              Parcelas
              <input
                type="number"
                min="1"
                max="48"
                required
                value={parcelaTotal}
                onChange={(e) => setParcelaTotal(e.target.value)}
              />
            </label>
            <label className="campo">
              1ª parcela
              <input
                type="date"
                required
                value={dataPrimeiraParcela}
                onChange={(e) => setDataPrimeiraParcela(e.target.value)}
              />
            </label>
          </div>
        ) : (
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
        )}

        <label className="campo">
          Descrição {tipo === 'despesa' && pagamento === 'parcelado' && '(obrigatória)'}
          <input
            type="text"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            required={tipo === 'despesa' && pagamento === 'parcelado'}
          />
        </label>

        <label className="campo">
          Conta
          <select value={contaId} onChange={(e) => setContaId(e.target.value)} required>
            <option value="">Selecione…</option>
            {contas.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        </label>

        {tipo === 'reserva' &&
          (caixinhas.length === 0 ? (
            <p className="mensagem-erro">
              Você ainda não tem nenhuma caixinha cadastrada. Crie uma em Configurações.
            </p>
          ) : (
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
          ))}

        {tipo !== 'reserva' &&
          (categoriasElegiveis.length === 0 && tipo !== 'despesa' && tipo !== 'ajuste' ? (
            <p className="mensagem-erro">
              Crie uma categoria do tipo {rotuloTipoCategoria} em Configurações antes de lançar.
            </p>
          ) : (
            <div className="campo-linha">
              <label className="campo">
                Categoria
                <select
                  value={categoriaId}
                  onChange={(e) => {
                    setCategoriaId(e.target.value)
                    setSubcategoriaId('')
                  }}
                >
                  <option value="">Nenhuma</option>
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
          ))}

        {(tipo === 'despesa' || tipo === 'ajuste') && (
          <div className="campo-linha">
            <label className="campo">
              Estrutura de custo
              <select value={estruturaCusto} onChange={(e) => setEstruturaCusto(e.target.value as EstruturaCusto | '')}>
                <option value="">Nenhuma</option>
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
                value={meioPagamento}
                onChange={(e) => setMeioPagamento(e.target.value as MeioPagamento | '')}
                disabled={tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito'}
              >
                <option value="">Nenhum</option>
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
            {enviando ? 'Salvando…' : 'Salvar lançamento'}
          </button>
          <Link to="/dashboard" className="botao-secundario">
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  )
}
