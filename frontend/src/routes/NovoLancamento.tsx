import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import '../components/forms.css'
import { ApiError, apiFetch } from '../lib/api'
import { hojeLocal } from '../lib/formatar'
import {
  ESTRUTURAS,
  MEIOS_PAGAMENTO,
  derivarTipoLancamento,
  rotuloEstruturaCusto,
  rotuloMeioPagamento,
  rotuloTipoMovimento,
} from '../lib/rotulos'
import { encontrarQuaseDuplicata } from '../lib/texto'
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

function hoje() {
  return hojeLocal()
}

export function NovoLancamento() {
  const location = useLocation()
  const navigate = useNavigate()
  // item 44: evita que o efeito de reset-ao-trocar-tipo (abaixo) apague os
  // campos que acabaram de ser preenchidos por "Duplicar" quando o tipo
  // duplicado é diferente do padrão ('despesa')
  const pularResetDeTipoRef = useRef(false)
  // garante que o efeito de "Duplicar" só processa location.state.duplicar
  // uma vez — sem isso, o StrictMode (roda todo efeito 2x em dev, de
  // propósito) dispara a busca da despesa original 2x e o `navigate` que
  // limpa o state corre com a 2ª chamada; achado testando a Rodada 55
  // (despesa original do Estorno/Ressarcimento vinha vazia)
  const duplicarProcessadoRef = useRef(false)

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
  // item 58: despesa já coberta por uma retirada de caixinha — opcional,
  // só aparece quando marcado; nunca inferido automaticamente
  const [coberto, setCoberto] = useState(false)
  const [caixinhaOrigemId, setCaixinhaOrigemId] = useState('')
  // id da despesa de origem quando este formulário foi aberto via "Lançar
  // retirada agora" (Dashboard, card "Retiradas pendentes de caixinha") —
  // depois de salvar a retirada com sucesso, marca a despesa como resolvida
  const despesaOrigemRetiradaRef = useRef<string | null>(null)

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
  // true quando o erro acima é o 409 de hash_dedup (lançamento idêntico
  // a outro já existente) — oferece "lançar mesmo assim" em vez de só
  // bloquear, porque pode ser 2 transações reais e diferentes que só
  // coincidem em data/valor/descrição/conta/tipo (achado 2026-09-25
  // migrando dados reais, ver backend)
  const [duplicadoDetectado, setDuplicadoDetectado] = useState(false)
  const [sucesso, setSucesso] = useState(false)
  // true só depois de "Lançar outro igual" (item 44) — mostra o aviso
  // "copiado do lançamento anterior" acima do formulário
  const [avisoCopiado, setAvisoCopiado] = useState(false)

  // categoria é escolhida entre as do tipo compatível (receita/despesa/
  // investimento) — igual pra qualquer tipo de lançamento, sem parentesco
  // fixo (ver regra em backend/app/schemas/categorias.py)
  const tipoCategoriaEfetivo = useMemo(() => {
    const t = tipo === 'ajuste' ? 'despesa' : tipo
    return t === 'despesa' || t === 'receita' || t === 'investimento' ? t : null
  }, [tipo])

  const categoriasElegiveis = useMemo(() => {
    if (!tipoCategoriaEfetivo) return []
    return categorias.filter((c) => c.tipo === tipoCategoriaEfetivo)
  }, [categorias, tipoCategoriaEfetivo])

  const rotuloTipoCategoria =
    tipo === 'receita' ? 'Receita' : tipo === 'investimento' ? 'Investimento' : 'Despesa'

  const subcategoriasDaCategoria = useMemo(
    () => subcategorias.filter((s) => s.categoria_id === categoriaId),
    [subcategorias, categoriaId],
  )

  // atalhos de "mais usadas" — poupam navegar o select inteiro pras
  // categorias/subcategorias do dia a dia; recalculados no backend por
  // frequência de uso nos últimos ~6 meses (GET .../mais-usadas)
  const [categoriasMaisUsadas, setCategoriasMaisUsadas] = useState<Categoria[]>([])
  const [subcategoriasMaisUsadas, setSubcategoriasMaisUsadas] = useState<Subcategoria[]>([])

  // consulta rápida pra uniformizar a Descrição (item 43 do backlog): chip
  // com as mais usadas na categoria/subcategoria + aviso quando o texto
  // digitado é "quase igual" a uma já usada (Levenshtein, ver lib/texto.ts)
  const [descricoesSugeridas, setDescricoesSugeridas] = useState<string[]>([])
  const [avisoQuaseDuplicataDescartado, setAvisoQuaseDuplicataDescartado] = useState(false)

  const [criandoCategoria, setCriandoCategoria] = useState(false)
  const [novaCategoriaNome, setNovaCategoriaNome] = useState('')
  const [salvandoCategoria, setSalvandoCategoria] = useState(false)
  const [erroCategoria, setErroCategoria] = useState<string | null>(null)

  const [criandoSubcategoria, setCriandoSubcategoria] = useState(false)
  const [novaSubcategoriaNome, setNovaSubcategoriaNome] = useState('')
  const [novaSubcategoriaEstrutura, setNovaSubcategoriaEstrutura] = useState<EstruturaCusto | ''>('')
  const [salvandoSubcategoria, setSalvandoSubcategoria] = useState(false)
  const [erroSubcategoria, setErroSubcategoria] = useState<string | null>(null)

  useEffect(() => {
    // "cancelado" evita condição de corrida: trocar de tipo (ex: Despesa
    // → Reserva) dispara ESTE efeito com a categoria ainda antiga (o
    // reset de categoriaId só roda num efeito seguinte — ver "ao trocar
    // o tipo" abaixo) antes de disparar de novo já limpo; sem a guarda,
    // a resposta da 1ª chamada (categoria antiga) podia chegar DEPOIS do
    // `setCategoriasMaisUsadas([])` do efeito seguinte e sobrescrever o
    // estado limpo com chips de um tipo que não é mais o selecionado.
    let cancelado = false
    if (!tipoCategoriaEfetivo) {
      setCategoriasMaisUsadas([])
      return
    }
    apiFetch<Categoria[]>(`/categorias/mais-usadas?tipo=${tipoCategoriaEfetivo}`)
      .then((res) => {
        if (!cancelado) setCategoriasMaisUsadas(res)
      })
      .catch(() => {
        if (!cancelado) setCategoriasMaisUsadas([])
      })
    return () => {
      cancelado = true
    }
  }, [tipoCategoriaEfetivo])

  useEffect(() => {
    let cancelado = false
    if (!categoriaId) {
      setSubcategoriasMaisUsadas([])
      return
    }
    apiFetch<Subcategoria[]>(`/subcategorias/mais-usadas?categoria_id=${categoriaId}`)
      .then((res) => {
        if (!cancelado) setSubcategoriasMaisUsadas(res)
      })
      .catch(() => {
        if (!cancelado) setSubcategoriasMaisUsadas([])
      })
    return () => {
      cancelado = true
    }
  }, [categoriaId])

  useEffect(() => {
    // mesma guarda de corrida do efeito de categoriasMaisUsadas acima —
    // achado real 2026-10-12: trocar de Despesa (com categoria) pra
    // Reserva deixava os chips de descrição da despesa anterior
    // aparecendo por cima dos de caixinha, porque a resposta da
    // categoria antiga chegava depois do `setDescricoesSugeridas([])`.
    let cancelado = false
    // reserva não usa categoria/subcategoria — agrupa por caixinha; o
    // `tipo === 'reserva'` evita usar um caixinhaId que sobrou de uma
    // escolha anterior depois de trocar pra outro tipo de lançamento
    const usarCaixinha = tipo === 'reserva' && !!caixinhaId
    if (!categoriaId && !usarCaixinha) {
      setDescricoesSugeridas([])
      return
    }
    const params = new URLSearchParams({ limite: '20' })
    if (subcategoriaId) {
      params.set('subcategoria_id', subcategoriaId)
    } else if (categoriaId) {
      params.set('categoria_id', categoriaId)
    } else {
      params.set('caixinha_id', caixinhaId)
    }
    apiFetch<string[]>(`/transacoes/descricoes-mais-usadas?${params.toString()}`)
      .then((res) => {
        if (!cancelado) setDescricoesSugeridas(res)
      })
      .catch(() => {
        if (!cancelado) setDescricoesSugeridas([])
      })
    return () => {
      cancelado = true
    }
  }, [categoriaId, subcategoriaId, caixinhaId, tipo])

  const descricaoQuaseDuplicata = useMemo(
    () => (avisoQuaseDuplicataDescartado ? null : encontrarQuaseDuplicata(descricao, descricoesSugeridas)),
    [descricao, descricoesSugeridas, avisoQuaseDuplicataDescartado],
  )

  function usarDescricaoSugerida(texto: string) {
    setDescricao(texto)
    setAvisoQuaseDuplicataDescartado(true)
  }

  function escolherCategoria(id: string) {
    setCategoriaId(id)
    setSubcategoriaId('')
    setCriandoCategoria(false)
  }

  async function criarCategoria() {
    const nome = novaCategoriaNome.trim()
    if (!nome || !tipoCategoriaEfetivo) return
    setSalvandoCategoria(true)
    setErroCategoria(null)
    try {
      const nova = await apiFetch<Categoria>('/categorias', {
        method: 'POST',
        body: JSON.stringify({ nome, tipo: tipoCategoriaEfetivo }),
      })
      setCategorias((prev) => [...prev, nova].sort((a, b) => a.nome.localeCompare(b.nome)))
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
    if (!nome || !categoriaId) return
    setSalvandoSubcategoria(true)
    setErroSubcategoria(null)
    try {
      const nova = await apiFetch<Subcategoria>('/subcategorias', {
        method: 'POST',
        body: JSON.stringify({
          nome,
          categoria_id: categoriaId,
          estrutura_custo_padrao: novaSubcategoriaEstrutura || null,
        }),
      })
      setSubcategorias((prev) => [...prev, nova].sort((a, b) => a.nome.localeCompare(b.nome)))
      selecionarSubcategoria(nova.id)
      setNovaSubcategoriaNome('')
      setNovaSubcategoriaEstrutura('')
      setCriandoSubcategoria(false)
    } catch (e) {
      setErroSubcategoria(e instanceof ApiError ? e.message : 'Falha ao criar subcategoria.')
    } finally {
      setSalvandoSubcategoria(false)
    }
  }

  const contaSelecionada = useMemo(() => contas.find((c) => c.id === contaId), [contas, contaId])
  const caixinhaSelecionada = useMemo(() => caixinhas.find((c) => c.id === caixinhaId), [caixinhas, caixinhaId])

  // recap do que foi salvo, pra tela de sucesso (item 44) — os campos não
  // são limpos depois de um submit bem-sucedido, então o estado atual já
  // É o que acabou de ser enviado
  const resumoUltimoLancamento = useMemo(() => {
    const tipoMovimento: TipoMovimento =
      tipo === 'ajuste' ? ajusteTipo : tipo === 'investimento' || tipo === 'reserva' ? direcao : tipo
    const nomeCategoria = categoriaId ? categorias.find((c) => c.id === categoriaId)?.nome : undefined
    const nomeSubcategoria = subcategoriaId ? subcategorias.find((s) => s.id === subcategoriaId)?.nome : undefined
    const nomeCaixinha = caixinhaId ? caixinhas.find((c) => c.id === caixinhaId)?.nome : undefined
    const valorExibido = tipo === 'despesa' && pagamento === 'parcelado' ? valorTotal : valor

    const detalhes = [
      rotuloTipoMovimento(tipoMovimento),
      nomeCategoria && nomeSubcategoria ? `${nomeCategoria} › ${nomeSubcategoria}` : nomeCategoria,
      nomeCaixinha,
      contaSelecionada?.nome,
      meioPagamento ? rotuloMeioPagamento(meioPagamento) : null,
      estruturaCusto ? rotuloEstruturaCusto(estruturaCusto) : null,
    ].filter(Boolean)

    return {
      titulo: descricao.trim() || '(sem descrição)',
      valor: valorExibido,
      detalhes: detalhes.join(' · '),
    }
  }, [
    tipo,
    ajusteTipo,
    direcao,
    pagamento,
    categoriaId,
    subcategoriaId,
    caixinhaId,
    categorias,
    subcategorias,
    caixinhas,
    contaSelecionada,
    meioPagamento,
    estruturaCusto,
    descricao,
    valor,
    valorTotal,
  ])

  // ao trocar o tipo, a categoria elegível muda — limpa a escolha anterior;
  // investimento tem estrutura de custo fixa, independente da categoria
  useEffect(() => {
    if (pularResetDeTipoRef.current) {
      pularResetDeTipoRef.current = false
      return
    }
    setCategoriaId('')
    setSubcategoriaId('')
    setEstruturaCusto(tipo === 'investimento' ? 'investimentos' : '')
    setCriandoCategoria(false)
    setCriandoSubcategoria(false)
    setNovaSubcategoriaEstrutura('')
    setCoberto(false)
    setCaixinhaOrigemId('')
    setAvisoQuaseDuplicataDescartado(false)
    setAvisoCopiado(false)
  }, [tipo])

  // despesa numa conta de cartão de crédito só pode ter sido paga no
  // cartão — trava o campo em vez de deixar escolher outra coisa
  useEffect(() => {
    if (tipo === 'despesa' && contaSelecionada?.tipo_conta === 'cartao_credito') {
      setMeioPagamento('cartao_credito')
    }
  }, [tipo, contaSelecionada])

  // caixinha vinculada a uma conta "mora" nessa conta — trava a conta do
  // lançamento na conta da caixinha em vez de deixar escolher outra
  useEffect(() => {
    if (tipo === 'reserva' && caixinhaSelecionada?.conta_id) {
      setContaId(caixinhaSelecionada.conta_id)
    }
  }, [tipo, caixinhaSelecionada])

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

  // item 44: "Duplicar" na lista de Lançamentos manda pra cá com a
  // transação original em location.state — pré-preenche tudo, exceto
  // valor (mesmo padrão de "Lançar outro igual"), e sempre como à vista
  // (repetir o parcelamento exigiria recalcular valor_total/parcelas,
  // fora de escopo — usuário escolhe "Parcelado" de novo se quiser)
  useEffect(() => {
    if (duplicarProcessadoRef.current) return
    const duplicar = (location.state as { duplicar?: Transacao } | null)?.duplicar
    if (!duplicar) return
    duplicarProcessadoRef.current = true

    const tipoDuplicado = derivarTipoLancamento(duplicar)
    // só pula o reset se o tipo for realmente mudar — setTipo com o mesmo
    // valor não dispara o efeito de reset (React não rerenderiza em valor
    // igual), e a flag ficaria "true" pendurada, quebrando a próxima troca
    // manual de tipo
    if (tipoDuplicado !== tipo) {
      pularResetDeTipoRef.current = true
    }
    setTipo(tipoDuplicado)
    if (duplicar.tipo_movimento === 'estorno' || duplicar.tipo_movimento === 'ressarcimento') {
      setAjusteTipo(duplicar.tipo_movimento)
    }
    if (duplicar.tipo_movimento === 'aplicacao' || duplicar.tipo_movimento === 'retirada') {
      setDirecao(duplicar.tipo_movimento)
    }
    setPagamento('avista')
    setDataCompra(duplicar.data_compra)
    setDescricao(duplicar.descricao ?? '')
    setContaId(duplicar.conta_id)
    setCategoriaId(duplicar.categoria_id ?? '')
    setSubcategoriaId(duplicar.subcategoria_id ?? '')
    setEstruturaCusto(duplicar.estrutura_custo ?? '')
    setCaixinhaId(duplicar.caixinha_id ?? '')
    setMeioPagamento(duplicar.meio_pagamento ?? '')
    setAvisoCopiado(true)

    if (duplicar.ajuste_de_transacao_id) {
      apiFetch<Transacao>(`/transacoes/${duplicar.ajuste_de_transacao_id}`)
        .then(selecionarDespesaOriginal)
        .catch(() => {})
    }

    // limpa o state da navegação — se o usuário voltar pra essa rota
    // depois (ex: botão "voltar" do navegador), não reaplica sozinho
    navigate(location.pathname, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // item 58: "Lançar retirada" (Dashboard, card "Retiradas pendentes de
  // caixinha") manda pra cá com a caixinha/valor já definidos em
  // location.state — mesmo padrão de "Duplicar" acima.
  // despesaOrigemRetiradaRef guarda o id da despesa original, usado em
  // handleSubmit pra marcar a retirada como feita só depois do POST
  // de verdade ter sucesso (nunca antes — evita marcar resolvido um
  // lançamento que falhou ao salvar).
  const prefillRetiradaProcessadoRef = useRef(false)
  useEffect(() => {
    if (prefillRetiradaProcessadoRef.current) return
    const prefill = (
      location.state as {
        prefillRetirada?: { caixinhaId: string; valor: number; descricaoSugestao: string; despesaOrigemId: string }
      } | null
    )?.prefillRetirada
    if (!prefill) return
    prefillRetiradaProcessadoRef.current = true

    if (tipo !== 'reserva') {
      pularResetDeTipoRef.current = true
    }
    setTipo('reserva')
    setDirecao('retirada')
    // conta não é setada aqui de propósito — o efeito que já existe
    // (caixinha vinculada a uma conta "trava" a conta do lançamento)
    // cuida disso sozinho assim que `caixinhaId` muda, mesmo caminho que
    // escolher a caixinha manualmente já passa
    setCaixinhaId(prefill.caixinhaId)
    setValor(String(prefill.valor))
    setDescricao(prefill.descricaoSugestao)
    despesaOrigemRetiradaRef.current = prefill.despesaOrigemId

    navigate(location.pathname, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
    setCriandoCategoria(false)
    setCriandoSubcategoria(false)
    setNovaSubcategoriaEstrutura('')
    setCaixinhaId('')
    setMeioPagamento('')
    setCoberto(false)
    setCaixinhaOrigemId('')
    despesaOrigemRetiradaRef.current = null
    setValorTotal('')
    setParcelaTotal('2')
    setDataPrimeiraParcela(hoje())
    trocarDespesaOriginal()
    setSucesso(false)
    setDuplicadoDetectado(false)
    setAvisoQuaseDuplicataDescartado(false)
    setAvisoCopiado(false)
  }

  // item 44: ao contrário de resetarFormulario, mantém tudo (tipo, conta,
  // categoria/subcategoria, estrutura de custo, meio de pagamento,
  // descrição, data) exatamente como foi submetido — já que nenhum desses
  // campos é limpo depois de salvar com sucesso — e limpa só o valor, o
  // campo que quase sempre muda entre lançamentos repetidos
  function lancarOutroIgual() {
    setValor('')
    setValorTotal('')
    setSucesso(false)
    setErro(null)
    setDuplicadoDetectado(false)
    setAvisoQuaseDuplicataDescartado(false)
    setAvisoCopiado(true)
  }

  // "Cancelar" volta pra onde o usuário estava antes de abrir o
  // formulário (FAB "+" em qualquer tela, "Duplicar" em Lançamentos,
  // nav principal) em vez de mandar sempre pro Dashboard — reportado
  // 2026-10-11: ao abrir pelo "+" estando em Lançamentos, Cancelar
  // levava pro Dashboard em vez de voltar pra onde estava.
  // window.history.length é uma estimativa (não dá pra saber com certeza
  // se há uma entrada anterior dentro do app) — no caso raro de não
  // haver, cai no Dashboard como antes.
  function cancelar() {
    if (window.history.length > 2) {
      navigate(-1)
    } else {
      navigate('/dashboard')
    }
  }

  function montarPayloadAvista(): Record<string, unknown> {
    const tipoMovimento: TipoMovimento =
      tipo === 'ajuste' ? ajusteTipo : tipo === 'investimento' || tipo === 'reserva' ? direcao : tipo
    return {
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
      caixinha_origem_id: tipo === 'despesa' && coberto ? caixinhaOrigemId || null : null,
      // item 58: só vem preenchido quando a retirada nasceu do prefill
      // "Lançar retirada" do Dashboard — permite reabrir o lembrete na
      // despesa de origem se essa retirada for excluída depois.
      despesa_origem_retirada_id: tipoMovimento === 'retirada' ? despesaOrigemRetiradaRef.current : null,
    }
  }

  function montarPayloadParcelada(): Record<string, unknown> {
    return {
      descricao,
      valor_total: Number(valorTotal),
      parcela_total: Number(parcelaTotal),
      data_primeira_parcela: dataPrimeiraParcela,
      conta_id: contaId,
      categoria_id: categoriaId || null,
      subcategoria_id: subcategoriaId || null,
      estrutura_custo: estruturaCusto || null,
      meio_pagamento: meioPagamento || null,
    }
  }

  async function handleForcarDuplicado() {
    setEnviando(true)
    setErro(null)
    try {
      if (tipo === 'despesa' && pagamento === 'parcelado') {
        await apiFetch('/transacoes/parceladas', {
          method: 'POST',
          body: JSON.stringify({ ...montarPayloadParcelada(), forcar_duplicado: true }),
        })
      } else {
        await apiFetch('/transacoes', {
          method: 'POST',
          body: JSON.stringify({ ...montarPayloadAvista(), forcar_duplicado: true }),
        })
      }
      setSucesso(true)
      setDuplicadoDetectado(false)
    } catch (e) {
      setErro(e instanceof ApiError ? (typeof e.detail === 'string' ? e.detail : e.message) : 'Falha ao salvar o lançamento.')
    } finally {
      setEnviando(false)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    setDuplicadoDetectado(false)

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
    if (tipo === 'despesa' && coberto && !caixinhaOrigemId) {
      setErro('Escolha a caixinha, ou desmarque "já estava guardada numa caixinha".')
      return
    }

    setEnviando(true)
    try {
      if (tipo === 'despesa' && pagamento === 'parcelado') {
        if (!descricao.trim()) {
          throw new ApiError(422, 'Descrição é obrigatória em compra parcelada.')
        }
        await apiFetch('/transacoes/parceladas', { method: 'POST', body: JSON.stringify(montarPayloadParcelada()) })
      } else {
        await apiFetch('/transacoes', { method: 'POST', body: JSON.stringify(montarPayloadAvista()) })
      }
      // item 58: só marca a retirada como feita DEPOIS do lançamento ter
      // sido salvo de verdade — uma falha aqui não deveria impedir a
      // retirada já criada de aparecer pro usuário (erro fica só num
      // console.error, não bloqueia a tela de sucesso)
      if (despesaOrigemRetiradaRef.current) {
        apiFetch(`/transacoes/${despesaOrigemRetiradaRef.current}/retirada-pendente`, {
          method: 'PATCH',
          body: JSON.stringify({ pendente: false }),
        }).catch((e) => console.error('Falha ao marcar retirada como feita na despesa de origem:', e))
      }
      setSucesso(true)
    } catch (e) {
      if (e instanceof ApiError) {
        setErro(typeof e.detail === 'string' ? e.detail : e.message)
        setDuplicadoDetectado(e.status === 409)
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
        <div className="recap-lancamento">
          <strong>
            {resumoUltimoLancamento.titulo}
            {resumoUltimoLancamento.valor && ` · R$ ${resumoUltimoLancamento.valor}`}
          </strong>
          <span>{resumoUltimoLancamento.detalhes}</span>
        </div>
        <div className="form-acoes form-acoes-coluna">
          <button type="button" className="botao-primario" onClick={lancarOutroIgual}>
            Lançar outro igual
          </button>
          <button type="button" className="botao-secundario" onClick={resetarFormulario}>
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

      {avisoCopiado && (
        <p className="aviso-copiado">Copiado do lançamento anterior — ajuste o valor (e a data, se for outro dia).</p>
      )}

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
                  onChange={(e) => escolherCategoria(e.target.value)}
                  required={tipo === 'despesa'}
                >
                  <option value="">{tipo === 'despesa' ? 'Selecione…' : 'Nenhuma'}</option>
                  {categoriasElegiveis.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
                {categoriasMaisUsadas.length > 0 && (
                  <div className="chips-rapidos">
                    {categoriasMaisUsadas
                      .filter((c) => c.id !== categoriaId)
                      .map((c) => (
                        <button key={c.id} type="button" className="chip" onClick={() => escolherCategoria(c.id)}>
                          {c.nome}
                        </button>
                      ))}
                    <button
                      type="button"
                      className="chip chip-criar"
                      onClick={() => setCriandoCategoria((v) => !v)}
                    >
                      + Nova
                    </button>
                  </div>
                )}
                {categoriasMaisUsadas.length === 0 && (
                  <button
                    type="button"
                    className="chip chip-criar chip-solta"
                    onClick={() => setCriandoCategoria((v) => !v)}
                  >
                    + Nova categoria
                  </button>
                )}
                {criandoCategoria && (
                  <div className="chip-form">
                    <input
                      type="text"
                      placeholder={`Nome da categoria de ${rotuloTipoCategoria.toLowerCase()}`}
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
                {categoriaId && (
                  <div className="chips-rapidos">
                    {subcategoriasMaisUsadas
                      .filter((s) => s.id !== subcategoriaId)
                      .map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          className="chip"
                          onClick={() => selecionarSubcategoria(s.id)}
                        >
                          {s.nome}
                        </button>
                      ))}
                    <button
                      type="button"
                      className="chip chip-criar"
                      onClick={() => setCriandoSubcategoria((v) => !v)}
                    >
                      + Nova
                    </button>
                  </div>
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
                    {tipoCategoriaEfetivo === 'despesa' && (
                      <select
                        value={novaSubcategoriaEstrutura}
                        onChange={(e) => setNovaSubcategoriaEstrutura(e.target.value as EstruturaCusto | '')}
                        title="Estrutura de custo padrão — sugerida sozinha nos próximos lançamentos com essa subcategoria"
                      >
                        <option value="">Estrutura padrão (opcional)</option>
                        {ESTRUTURAS.filter((e) => e.valor !== 'investimentos').map((e) => (
                          <option key={e.valor} value={e.valor}>
                            {e.rotulo}
                          </option>
                        ))}
                      </select>
                    )}
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
          ))}

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

        <label className="campo">
          Descrição {tipo === 'despesa' && pagamento === 'parcelado' && '(obrigatória)'}
          <input
            type="text"
            value={descricao}
            onChange={(e) => {
              setDescricao(e.target.value)
              setAvisoQuaseDuplicataDescartado(false)
            }}
            required={tipo === 'despesa' && pagamento === 'parcelado'}
          />
          {descricoesSugeridas.length > 0 && (
            <div className="chips-rapidos">
              {descricoesSugeridas
                .slice(0, 5)
                .filter((d) => d !== descricao)
                .map((d) => (
                  <button key={d} type="button" className="chip" onClick={() => usarDescricaoSugerida(d)}>
                    {d}
                  </button>
                ))}
            </div>
          )}
          {descricaoQuaseDuplicata && (
            <div className="aviso-quase-duplicata">
              <span>
                Você já usou <strong>"{descricaoQuaseDuplicata}"</strong> nessa categoria/subcategoria. Quis dizer
                isso?
              </span>
              <div className="form-acoes">
                <button
                  type="button"
                  className="botao-secundario"
                  onClick={() => usarDescricaoSugerida(descricaoQuaseDuplicata)}
                >
                  Usar essa
                </button>
                <button
                  type="button"
                  className="chip-cancelar"
                  onClick={() => setAvisoQuaseDuplicataDescartado(true)}
                >
                  Manter a minha
                </button>
              </div>
            </div>
          )}
        </label>

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
                {/* 'investimentos' é fixada automaticamente só pro tipo Investimento — não é opção aqui */}
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

        {tipo === 'despesa' && (
          <div className="campo-caixinha-origem">
            <label className="checkbox-linha">
              <input type="checkbox" checked={coberto} onChange={(e) => setCoberto(e.target.checked)} />
              Essa despesa já estava guardada numa caixinha?
            </label>
            {coberto && (
              <label className="campo campo-caixinha-origem-select">
                Qual caixinha?
                <select value={caixinhaOrigemId} onChange={(e) => setCaixinhaOrigemId(e.target.value)} required>
                  <option value="">Selecione…</option>
                  {caixinhas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
                <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
                  Vai aparecer em "Retiradas pendentes" no Dashboard até você registrar o saque.
                </span>
              </label>
            )}
          </div>
        )}

        {erro && (
          <p role="alert" className="mensagem-erro">
            {erro}
          </p>
        )}
        {duplicadoDetectado && (
          <div className="form-acoes">
            <button type="button" className="botao-secundario" onClick={handleForcarDuplicado} disabled={enviando}>
              Lançar mesmo assim (é outro lançamento real)
            </button>
          </div>
        )}

        <div className="form-acoes">
          <button type="submit" className="botao-primario" disabled={enviando}>
            {enviando ? 'Salvando…' : 'Salvar lançamento'}
          </button>
          <button type="button" className="botao-secundario" onClick={cancelar}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
