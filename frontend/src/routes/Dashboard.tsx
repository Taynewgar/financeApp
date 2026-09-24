import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { InfoIcon } from '../components/InfoIcon'
import { SeletorPeriodo } from '../components/SeletorPeriodo'
import { Sparkline } from '../components/Sparkline'
import '../components/forms.css'
import '../components/resumoCards.css'
import '../components/crud.css'
import '../components/dashboard.css'
import { useAuth } from '../auth/AuthContext'
import { ApiError, apiFetch } from '../lib/api'
import { formatarData, formatarMoeda } from '../lib/formatar'
import { mesesAntes, usePeriodo } from '../lib/periodo'
import { usePrivacidade } from '../lib/PrivacyContext'
import type {
  CamposFinanceiros,
  CompromissoFuturo,
  DespesaPorCategoria as DespesaPorCategoriaT,
  EvolucaoMensal,
  ResumoMensal,
  ResumoPeriodo,
  SaldoCaixinha,
} from '../lib/types'

type Leitura = 'caixa' | 'saude'

const EXPLICACAO: Record<string, string> = {
  fluxo_caixa: 'Receitas menos despesas brutas (sem descontar estornos) — o que de fato entrou e saiu das contas.',
  receitas: 'Soma de todos os lançamentos do tipo Receita no período.',
  despesas_brutas: 'Soma de todos os lançamentos do tipo Despesa no período, antes de qualquer estorno/ressarcimento.',
  reservas: 'Aplicações menos retiradas em caixinhas (com caixinha vinculada) — dinheiro guardado numa reserva.',
  investimentos: 'Aplicações menos retiradas sem caixinha vinculada — dinheiro investido, conceito diferente de reserva.',
  resultado_saude: 'Resultado do período (saúde financeira): receita mais ajustes soltos, menos despesas já líquidas dos estornos/ressarcimentos vinculados a elas.',
  receita_ajustada: 'Receitas mais estornos/ressarcimentos soltos (sem vínculo a uma despesa específica) — a base usada na leitura de saúde.',
  despesas_liquidas: 'Despesas menos estornos/ressarcimentos vinculados a elas — o quanto de fato saiu do bolso.',
  taxa_poupanca: 'Percentual da receita (já somando ajustes soltos) que sobrou depois das despesas líquidas.',
  meses_negativos: 'Quantos meses de janeiro até o mês de referência tiveram resultado (leitura de saúde) negativo.',
  maior_categoria_despesa: 'Categoria com maior soma de despesas no mês de referência — mesmo recorte do gráfico "Despesas por Categoria".',
}

function classeResultado(valor: number): string {
  return valor >= 0 ? 'valor-receita' : 'valor-despesa'
}

function receitaAjustada(r: CamposFinanceiros): number {
  return r.receitas + r.ajustes_nao_vinculados
}

/** Variação percentual vs mês anterior, em texto neutro (a cor já está no
 * valor absoluto do card — a seta some ambiguidade de "melhorou ou piorou"
 * sem precisar saber, métrica a métrica, se subir é bom ou ruim). */
function textoDelta(atual: number, anterior: number, oculto: boolean): string {
  if (anterior === 0) {
    return atual === 0
      ? 'Estável vs mês anterior'
      : `${atual > 0 ? '+' : ''}${formatarMoeda(atual, oculto)} vs mês anterior`
  }
  const variacao = ((atual - anterior) / Math.abs(anterior)) * 100
  if (Math.abs(variacao) < 0.05) return 'Estável vs mês anterior'
  const seta = variacao > 0 ? '↗' : '↘'
  return `${seta} ${Math.abs(variacao).toFixed(1)}% vs mês anterior`
}

export function Dashboard() {
  const { session } = useAuth()
  const { oculto } = usePrivacidade()

  const periodo = usePeriodo()
  const { modoData, vigenciaMes, primeiroMes, periodoInicio, periodoFim, mesReferencia } = periodo

  const [leitura, setLeitura] = useState<Leitura>('saude')
  const [resumo, setResumo] = useState<CamposFinanceiros | null>(null)
  const [mesAnterior, setMesAnterior] = useState<ResumoMensal | null>(null)
  const [evolucao, setEvolucao] = useState<EvolucaoMensal | null>(null)
  const [taxaAcumuladaAno, setTaxaAcumuladaAno] = useState<number | null>(null)
  const [resultadoAcumuladoAno, setResultadoAcumuladoAno] = useState<number | null>(null)
  const [mesesNegativosAno, setMesesNegativosAno] = useState<{ negativos: number; total: number } | null>(null)
  const [caixinhas, setCaixinhas] = useState<SaldoCaixinha[] | null>(null)
  const [compromissos, setCompromissos] = useState<CompromissoFuturo[] | null>(null)
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null)
  const [pulandoId, setPulandoId] = useState<string | null>(null)
  const [erroConfirmar, setErroConfirmar] = useState<string | null>(null)
  const [despesasCategoria, setDespesasCategoria] = useState<DespesaPorCategoriaT[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  function buscarCompromissos() {
    return apiFetch<CompromissoFuturo[]>('/dashboard/compromissos-futuros').then(setCompromissos).catch(() => setCompromissos([]))
  }

  // compromissos futuros não dependem do período navegado (é sempre "a partir de hoje")
  useEffect(() => {
    buscarCompromissos()
  }, [])

  // erro não é limpo no início da ação — só quando ELA MESMA termina (sucesso
  // limpa, falha substitui) — senão uma ação rápida em cima de outra apaga o
  // erro da anterior antes de dar tempo de ler (bug reportado 2026-09-24)
  async function confirmarRecorrente(c: CompromissoFuturo) {
    if (!c.lancamento_recorrente_id) return
    setConfirmandoId(c.lancamento_recorrente_id)
    try {
      await apiFetch(`/lancamentos-recorrentes/${c.lancamento_recorrente_id}/confirmar`, {
        method: 'POST',
        body: JSON.stringify({ vigencia_mes: `${c.data_compra.slice(0, 7)}-01` }),
      })
      setErroConfirmar(null)
      await buscarCompromissos()
    } catch (e) {
      setErroConfirmar(
        `Falha ao confirmar "${c.descricao ?? 'recorrente'}" (${formatarData(c.data_compra)}): ${e instanceof ApiError ? e.message : 'erro desconhecido'}`,
      )
    } finally {
      setConfirmandoId(null)
    }
  }

  async function pularRecorrente(c: CompromissoFuturo) {
    if (!c.lancamento_recorrente_id) return
    if (!window.confirm(`Marcar "${c.descricao ?? 'este recorrente'}" como não aplicável neste mês?`)) return
    setPulandoId(c.lancamento_recorrente_id)
    try {
      await apiFetch(`/lancamentos-recorrentes/${c.lancamento_recorrente_id}/pular`, {
        method: 'POST',
        body: JSON.stringify({ vigencia_mes: `${c.data_compra.slice(0, 7)}-01` }),
      })
      setErroConfirmar(null)
      await buscarCompromissos()
    } catch (e) {
      setErroConfirmar(
        `Falha ao pular "${c.descricao ?? 'recorrente'}" (${formatarData(c.data_compra)}): ${e instanceof ApiError ? e.message : 'erro desconhecido'}`,
      )
    } finally {
      setPulandoId(null)
    }
  }

  useEffect(() => {
    if (modoData === 'todos' && primeiroMes === null) return // aguarda carregar o início do histórico
    setErro(null)

    const evolucaoInicio = modoData === 'mes' ? mesesAntes(vigenciaMes, 5) : periodoInicio
    const evolucaoFim = periodoFim

    const buscaResumo =
      modoData === 'mes'
        ? apiFetch<ResumoMensal>(`/dashboard/mensal/${vigenciaMes}-01`)
        : apiFetch<ResumoPeriodo>(`/dashboard/resumo-periodo?inicio=${periodoInicio}-01&fim=${periodoFim}-01`)

    Promise.all([
      buscaResumo,
      apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${evolucaoInicio}-01&fim=${evolucaoFim}-01`),
      apiFetch<SaldoCaixinha[]>(`/dashboard/patrimonio/${mesReferencia}-01`),
      apiFetch<DespesaPorCategoriaT[]>(`/dashboard/despesas-por-categoria/${mesReferencia}-01`),
    ])
      .then(([r, e, c, d]) => {
        setResumo(r)
        setEvolucao(e)
        setCaixinhas(c)
        setDespesasCategoria(d)
        // penúltimo ponto da janela é o mês imediatamente anterior ao
        // selecionado (janela contígua) — só faz sentido comparar "mês
        // anterior" quando se está vendo 1 mês só
        setMesAnterior(modoData === 'mes' && e.meses.length >= 2 ? e.meses[e.meses.length - 2] : null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o dashboard'))
  }, [modoData, vigenciaMes, periodoInicio, periodoFim, mesReferencia, primeiroMes])

  // taxa/resultado acumulado e contagem de meses negativos NO ANO do mês de
  // referência — busca à parte porque é uma janela diferente (jan até o
  // mês de referência), independente do período navegado na tela
  useEffect(() => {
    const [ano] = mesReferencia.split('-')
    apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${ano}-01-01&fim=${mesReferencia}-01`)
      .then((e) => {
        const ultimo = e.meses.length ? e.meses[e.meses.length - 1] : null
        setTaxaAcumuladaAno(ultimo ? ultimo.taxa_poupanca_acumulada : null)
        setResultadoAcumuladoAno(ultimo ? ultimo.resultado_saude_acumulado : null)
        setMesesNegativosAno({
          negativos: e.meses.filter((m) => m.resultado_saude < 0).length,
          total: e.meses.length,
        })
      })
      .catch(() => {
        setTaxaAcumuladaAno(null)
        setResultadoAcumuladoAno(null)
        setMesesNegativosAno(null)
      })
  }, [mesReferencia])

  const maiorCategoriaDespesa = useMemo(() => {
    if (!despesasCategoria || despesasCategoria.length === 0) return null
    return despesasCategoria.reduce((maior, atual) => (atual.valor > maior.valor ? atual : maior))
  }, [despesasCategoria])

  const hero = resumo && (leitura === 'caixa' ? resumo.resultado_fluxo_caixa : resumo.resultado_saude)
  const heroAnterior =
    mesAnterior && (leitura === 'caixa' ? mesAnterior.resultado_fluxo_caixa : mesAnterior.resultado_saude)

  // meses já buscados pra "mês anterior" — reaproveitados como sparkline
  // nos KPIs (sem chamada nova); precisa de pelo menos 2 pontos pra formar linha
  const tendencia = evolucao && evolucao.meses.length >= 2 ? evolucao.meses : null

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 0 }}>Olá, {session?.user.email}</h1>
      </div>

      <SeletorPeriodo {...periodo} mostrarBaseMedia={false} />

      {erro && <p className="mensagem-erro">{erro}</p>}

      {resumo && (
        <>
          <div className="segmentado" style={{ margin: '16px 0 0' }}>
            <button type="button" className={leitura === 'caixa' ? 'ativo' : ''} onClick={() => setLeitura('caixa')}>
              Leitura de Caixa
            </button>
            <button type="button" className={leitura === 'saude' ? 'ativo' : ''} onClick={() => setLeitura('saude')}>
              Leitura de Saúde
            </button>
          </div>

          <div style={{ margin: '12px 0 20px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
                {leitura === 'caixa' ? 'Resultado de caixa' : 'Resultado de saúde'}
                <InfoIcon texto={EXPLICACAO[leitura === 'caixa' ? 'fluxo_caixa' : 'resultado_saude']} />
              </span>
              <div className={classeResultado(hero ?? 0)} style={{ fontSize: 48, fontWeight: 600, lineHeight: 1.1 }}>
                {formatarMoeda(hero ?? 0, oculto)}
              </div>
              {heroAnterior !== null && heroAnterior !== undefined && (
                <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>
                  {textoDelta(hero ?? 0, heroAnterior, oculto)}
                </span>
              )}
            </div>
            {tendencia && (
              <Sparkline
                valores={tendencia.map((m) => (leitura === 'caixa' ? m.resultado_fluxo_caixa : m.resultado_saude))}
              />
            )}
          </div>

          <div className="resumo-cards">
            {leitura === 'caixa' ? (
              <>
                <div className="resumo-card">
                  <span className="resumo-card-rotulo">
                    Receitas
                    <InfoIcon texto={EXPLICACAO.receitas} />
                  </span>
                  <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">{textoDelta(resumo.receitas, mesAnterior.receitas, oculto)}</span>
                  )}
                  {tendencia && (
                    <div className="resumo-card-sparkline">
                      <Sparkline valores={tendencia.map((m) => m.receitas)} />
                    </div>
                  )}
                </div>
                <div className="resumo-card">
                  <span className="resumo-card-rotulo">
                    Despesas
                    <InfoIcon texto={EXPLICACAO.despesas_brutas} />
                  </span>
                  <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_brutas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(resumo.despesas_brutas, mesAnterior.despesas_brutas, oculto)}
                    </span>
                  )}
                  {tendencia && (
                    <div className="resumo-card-sparkline">
                      <Sparkline valores={tendencia.map((m) => m.despesas_brutas)} />
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="resumo-card">
                  <span className="resumo-card-rotulo">
                    Receita ajustada
                    <InfoIcon texto={EXPLICACAO.receita_ajustada} />
                  </span>
                  <span className="resumo-card-valor valor-receita">{formatarMoeda(receitaAjustada(resumo), oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(receitaAjustada(resumo), receitaAjustada(mesAnterior), oculto)}
                    </span>
                  )}
                  {tendencia && (
                    <div className="resumo-card-sparkline">
                      <Sparkline valores={tendencia.map((m) => receitaAjustada(m))} />
                    </div>
                  )}
                </div>
                <div className="resumo-card">
                  <span className="resumo-card-rotulo">
                    Despesas líquidas
                    <InfoIcon texto={EXPLICACAO.despesas_liquidas} />
                  </span>
                  <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(resumo.despesas_liquidas, mesAnterior.despesas_liquidas, oculto)}
                    </span>
                  )}
                  {tendencia && (
                    <div className="resumo-card-sparkline">
                      <Sparkline valores={tendencia.map((m) => m.despesas_liquidas)} />
                    </div>
                  )}
                </div>
              </>
            )}

            <div className="resumo-card">
              <span className="resumo-card-rotulo">
                Reservas
                <InfoIcon texto={EXPLICACAO.reservas} />
              </span>
              <span className="resumo-card-valor valor-investimento">{formatarMoeda(resumo.reservas, oculto)}</span>
              {mesAnterior && (
                <span className="resumo-card-delta">{textoDelta(resumo.reservas, mesAnterior.reservas, oculto)}</span>
              )}
              {tendencia && (
                <div className="resumo-card-sparkline">
                  <Sparkline valores={tendencia.map((m) => m.reservas)} />
                </div>
              )}
            </div>
            <div className="resumo-card">
              <span className="resumo-card-rotulo">
                Investimentos
                <InfoIcon texto={EXPLICACAO.investimentos} />
              </span>
              <span className="resumo-card-valor valor-investimento">{formatarMoeda(resumo.investimentos, oculto)}</span>
              {mesAnterior && (
                <span className="resumo-card-delta">
                  {textoDelta(resumo.investimentos, mesAnterior.investimentos, oculto)}
                </span>
              )}
              {tendencia && (
                <div className="resumo-card-sparkline">
                  <Sparkline valores={tendencia.map((m) => m.investimentos)} />
                </div>
              )}
            </div>
            <div className="resumo-card">
              <span className="resumo-card-rotulo">
                Taxa de poupança
                <InfoIcon texto={EXPLICACAO.taxa_poupanca} />
              </span>
              <span className="resumo-card-valor">
                {resumo.taxa_poupanca === null ? '—' : `${resumo.taxa_poupanca.toFixed(1)}%`}
              </span>
              {mesAnterior && resumo.taxa_poupanca !== null && mesAnterior.taxa_poupanca !== null && (
                <span className="resumo-card-delta">
                  {textoDelta(resumo.taxa_poupanca, mesAnterior.taxa_poupanca, oculto)}
                </span>
              )}
              {taxaAcumuladaAno !== null && (
                <span className="resumo-card-delta">Acumulado no ano: {taxaAcumuladaAno.toFixed(1)}%</span>
              )}
              {resultadoAcumuladoAno !== null && (
                <span className="resumo-card-delta">
                  Resultado acumulado no ano: {formatarMoeda(resultadoAcumuladoAno, oculto)}
                </span>
              )}
              {tendencia && (
                <div className="resumo-card-sparkline">
                  <Sparkline valores={tendencia.filter((m) => m.taxa_poupanca !== null).map((m) => m.taxa_poupanca!)} />
                </div>
              )}
            </div>
            <div className="resumo-card">
              <span className="resumo-card-rotulo">
                Meses com resultado negativo
                <InfoIcon texto={EXPLICACAO.meses_negativos} />
              </span>
              <span className="resumo-card-valor">
                {mesesNegativosAno === null ? '—' : mesesNegativosAno.negativos}
              </span>
              {mesesNegativosAno !== null && (
                <span className="resumo-card-delta">de {mesesNegativosAno.total} meses no ano</span>
              )}
            </div>
            <div className="resumo-card">
              <span className="resumo-card-rotulo">
                Maior categoria de despesa
                <InfoIcon texto={EXPLICACAO.maior_categoria_despesa} />
              </span>
              <span className="resumo-card-valor valor-despesa">
                {maiorCategoriaDespesa ? maiorCategoriaDespesa.categoria_nome : '—'}
              </span>
              {maiorCategoriaDespesa && (
                <span className="resumo-card-delta">{formatarMoeda(maiorCategoriaDespesa.valor, oculto)}</span>
              )}
            </div>
          </div>
        </>
      )}

      {resumo === null && !erro && <p>Carregando…</p>}

      {resumo && (
        <div className="dashboard-secoes">
          <div className="dashboard-secao">
            <h2 style={{ fontSize: 16, marginTop: 0, marginBottom: 8 }}>Patrimônio em Caixinhas</h2>
            <p style={{ fontSize: 12, color: 'var(--cor-texto-suave)', marginTop: 0 }}>
              Contas ainda não têm saldo próprio nesta versão — só caixinhas.
            </p>
            {caixinhas === null ? (
              <p>Carregando…</p>
            ) : caixinhas.length === 0 ? (
              <p style={{ color: 'var(--cor-texto-suave)' }}>Nenhuma caixinha cadastrada ainda.</p>
            ) : (
              <ul className="lista-crud">
                {caixinhas.map((c) => (
                  <li key={c.id}>
                    <div className="item-linha">
                      <div className="item-info">
                        <span className="item-titulo">{c.nome}</span>
                        <span className="item-detalhe">Caixinha</span>
                      </div>
                      <span className="resumo-card-valor valor-investimento">{formatarMoeda(c.saldo, oculto)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="dashboard-secao">
            <h2 style={{ fontSize: 16, marginTop: 0, marginBottom: 8 }}>Compromissos Futuros</h2>
            {erroConfirmar && <p className="mensagem-erro">{erroConfirmar}</p>}
            {compromissos === null ? (
              <p>Carregando…</p>
            ) : compromissos.length === 0 ? (
              <p style={{ color: 'var(--cor-texto-suave)' }}>Nenhum compromisso futuro em aberto.</p>
            ) : (
              <ul className="lista-crud">
                {compromissos.map((c, i) => (
                  <li key={i}>
                    <div className="item-linha">
                      <div className="item-info">
                        <span className="item-titulo">{c.descricao ?? 'Sem descrição'}</span>
                        <span className="item-detalhe">
                          {c.tipo === 'parcela'
                            ? `Parcela ${c.parcela_atual} de ${c.parcela_total}`
                            : 'Despesa fixa recorrente'}{' '}
                          · {formatarData(c.data_compra)}
                        </span>
                      </div>
                      <span className="resumo-card-valor valor-despesa">{formatarMoeda(c.valor, oculto)}</span>
                      {c.tipo === 'recorrente' && (
                        // colunas + gap maior (em vez do .item-acoes padrão lado a lado)
                        // pra reduzir o risco de clicar em "pular" querendo "confirmar" —
                        // bug reportado 2026-09-24
                        <div className="item-acoes" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 4 }}>
                          <button
                            type="button"
                            className="botao-secundario"
                            disabled={confirmandoId === c.lancamento_recorrente_id || pulandoId === c.lancamento_recorrente_id}
                            onClick={() => confirmarRecorrente(c)}
                          >
                            {confirmandoId === c.lancamento_recorrente_id ? 'Confirmando…' : 'Confirmar'}
                          </button>
                          <button
                            type="button"
                            className="botao-link"
                            title="Marcar esse mês como não aplicável (ex: viajou, não teve a despesa)"
                            style={{ fontSize: 12, color: 'var(--cor-texto-suave)', marginTop: 6 }}
                            disabled={confirmandoId === c.lancamento_recorrente_id || pulandoId === c.lancamento_recorrente_id}
                            onClick={() => pularRecorrente(c)}
                          >
                            {pulandoId === c.lancamento_recorrente_id ? 'Pulando…' : 'Pular este mês'}
                          </button>
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {resumo && (
        <p style={{ marginTop: 4 }}>
          <Link to="/graficos" className="botao-secundario">
            Ver gráficos completos →
          </Link>
        </p>
      )}
    </div>
  )
}
