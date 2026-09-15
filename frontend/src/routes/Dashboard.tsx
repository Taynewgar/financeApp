import { useEffect, useMemo, useState } from 'react'
import { BotaoPrivacidade } from '../components/BotaoPrivacidade'
import { DespesasPorCategoria } from '../components/DespesasPorCategoria'
import { EvolucaoChart } from '../components/EvolucaoChart'
import '../components/forms.css'
import '../components/resumoCards.css'
import '../components/crud.css'
import '../components/dashboard.css'
import { useAuth } from '../auth/AuthContext'
import { ApiError, apiFetch } from '../lib/api'
import { formatarData, formatarMoeda } from '../lib/formatar'
import { usePrivacidade } from '../lib/PrivacyContext'
import type {
  CamposFinanceiros,
  CompromissoFuturo,
  DespesaPorCategoria as DespesaPorCategoriaT,
  EvolucaoMensal,
  PrimeiroMes,
  ResumoMensal,
  ResumoPeriodo,
  SaldoCaixinha,
} from '../lib/types'

type Leitura = 'caixa' | 'saude'
type ModoData = 'mes' | 'intervalo' | 'todos'
type BaseMedia = 'ate_mes' | 'todos_meses'

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
  base_media: 'Ainda sem efeito nos cálculos — vai orientar médias de gráficos/KPIs quando essa funcionalidade existir.',
}

const MESES_NOME = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]

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

function rotuloMesLongo(anoMes: string): string {
  const [ano, mes] = anoMes.split('-').map(Number)
  return `${MESES_NOME[mes - 1]} de ${ano}`
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

  const [modoData, setModoData] = useState<ModoData>('mes')
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [intervaloInicio, setIntervaloInicio] = useState(mesesAntes(hojeAnoMes(), 2))
  const [intervaloFim, setIntervaloFim] = useState(hojeAnoMes())
  const [baseMedia, setBaseMedia] = useState<BaseMedia>('ate_mes')
  const [primeiroMes, setPrimeiroMes] = useState<string | null>(null)

  const [leitura, setLeitura] = useState<Leitura>('saude')
  const [resumo, setResumo] = useState<CamposFinanceiros | null>(null)
  const [mesAnterior, setMesAnterior] = useState<ResumoMensal | null>(null)
  const [evolucao, setEvolucao] = useState<EvolucaoMensal | null>(null)
  const [taxaAcumuladaAno, setTaxaAcumuladaAno] = useState<number | null>(null)
  const [caixinhas, setCaixinhas] = useState<SaldoCaixinha[] | null>(null)
  const [compromissos, setCompromissos] = useState<CompromissoFuturo[] | null>(null)
  const [despesasCategoria, setDespesasCategoria] = useState<DespesaPorCategoriaT[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  // "Todos os meses" precisa saber onde o histórico começa
  useEffect(() => {
    apiFetch<PrimeiroMes>('/dashboard/primeiro-mes')
      .then((p) => setPrimeiroMes(p.vigencia_mes ? p.vigencia_mes.slice(0, 7) : hojeAnoMes()))
      .catch(() => setPrimeiroMes(hojeAnoMes()))
  }, [])

  // compromissos futuros não dependem do período navegado (é sempre "a partir de hoje")
  useEffect(() => {
    apiFetch<CompromissoFuturo[]>('/dashboard/compromissos-futuros').then(setCompromissos).catch(() => setCompromissos([]))
  }, [])

  const { periodoInicio, periodoFim, mesReferencia } = useMemo(() => {
    if (modoData === 'mes') return { periodoInicio: vigenciaMes, periodoFim: vigenciaMes, mesReferencia: vigenciaMes }
    if (modoData === 'intervalo') return { periodoInicio: intervaloInicio, periodoFim: intervaloFim, mesReferencia: intervaloFim }
    // "Todos os meses" é sempre até hoje, independente do que ficou
    // selecionado no modo Mês antes de trocar de aba — vigenciaMes pode ser
    // qualquer mês navegado (até sem dado nenhum), inclusive anterior ao
    // primeiro lançamento real, o que quebrava a conta (fim antes do início)
    const hoje = hojeAnoMes()
    return { periodoInicio: primeiroMes ?? hoje, periodoFim: hoje, mesReferencia: hoje }
  }, [modoData, vigenciaMes, intervaloInicio, intervaloFim, primeiroMes])

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

  // taxa de poupança acumulada NO ANO do mês de referência — busca à parte
  // porque é uma janela diferente (jan até o mês de referência)
  useEffect(() => {
    const [ano] = mesReferencia.split('-')
    apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${ano}-01-01&fim=${mesReferencia}-01`)
      .then((e) => setTaxaAcumuladaAno(e.meses.length ? e.meses[e.meses.length - 1].taxa_poupanca_acumulada : null))
      .catch(() => setTaxaAcumuladaAno(null))
  }, [mesReferencia])

  const hero = resumo && (leitura === 'caixa' ? resumo.resultado_fluxo_caixa : resumo.resultado_saude)
  const heroAnterior =
    mesAnterior && (leitura === 'caixa' ? mesAnterior.resultado_fluxo_caixa : mesAnterior.resultado_saude)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 0 }}>Olá, {session?.user.email}</h1>
      </div>

      <div className="dashboard-seletor">
        <div className="segmentado">
          <button type="button" className={modoData === 'mes' ? 'ativo' : ''} onClick={() => setModoData('mes')}>
            Mês
          </button>
          <button type="button" className={modoData === 'intervalo' ? 'ativo' : ''} onClick={() => setModoData('intervalo')}>
            Intervalo
          </button>
          <button type="button" className={modoData === 'todos' ? 'ativo' : ''} onClick={() => setModoData('todos')}>
            Todos os meses
          </button>
        </div>

        <BotaoPrivacidade />

        {modoData === 'mes' && (
          <label className="campo" style={{ maxWidth: 180 }}>
            Mês
            <input type="month" value={vigenciaMes} onChange={(e) => setVigenciaMes(e.target.value)} max={hojeAnoMes()} />
          </label>
        )}

        {modoData === 'intervalo' && (
          <div className="campo-linha">
            <label className="campo" style={{ maxWidth: 180 }}>
              Início
              <input
                type="month"
                value={intervaloInicio}
                onChange={(e) => setIntervaloInicio(e.target.value)}
                max={intervaloFim}
              />
            </label>
            <label className="campo" style={{ maxWidth: 180 }}>
              Fim
              <input
                type="month"
                value={intervaloFim}
                onChange={(e) => setIntervaloFim(e.target.value)}
                min={intervaloInicio}
                max={hojeAnoMes()}
              />
            </label>
          </div>
        )}

        {modoData === 'todos' && (
          <p style={{ fontSize: 13, color: 'var(--cor-texto-suave)', margin: 0 }}>
            {primeiroMes
              ? `Desde ${rotuloMesLongo(primeiroMes)} até ${rotuloMesLongo(hojeAnoMes())}`
              : 'Carregando período…'}
          </p>
        )}

        {modoData !== 'mes' && (
          <div className="campo" title={EXPLICACAO.base_media}>
            <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>Base da média</span>
            <div className="segmentado">
              <button type="button" className={baseMedia === 'ate_mes' ? 'ativo' : ''} onClick={() => setBaseMedia('ate_mes')}>
                Até o mês
              </button>
              <button
                type="button"
                className={baseMedia === 'todos_meses' ? 'ativo' : ''}
                onClick={() => setBaseMedia('todos_meses')}
              >
                Todos os meses
              </button>
            </div>
          </div>
        )}
      </div>

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

          <div title={EXPLICACAO[leitura === 'caixa' ? 'fluxo_caixa' : 'resultado_saude']} style={{ margin: '12px 0 20px' }}>
            <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
              {leitura === 'caixa' ? 'Resultado de caixa' : 'Resultado de saúde'}
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

          <div className="resumo-cards">
            {leitura === 'caixa' ? (
              <>
                <div className="resumo-card" title={EXPLICACAO.receitas}>
                  <span className="resumo-card-rotulo">Receitas</span>
                  <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">{textoDelta(resumo.receitas, mesAnterior.receitas, oculto)}</span>
                  )}
                </div>
                <div className="resumo-card" title={EXPLICACAO.despesas_brutas}>
                  <span className="resumo-card-rotulo">Despesas</span>
                  <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_brutas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(resumo.despesas_brutas, mesAnterior.despesas_brutas, oculto)}
                    </span>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="resumo-card" title={EXPLICACAO.receita_ajustada}>
                  <span className="resumo-card-rotulo">Receita ajustada</span>
                  <span className="resumo-card-valor valor-receita">{formatarMoeda(receitaAjustada(resumo), oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(receitaAjustada(resumo), receitaAjustada(mesAnterior), oculto)}
                    </span>
                  )}
                </div>
                <div className="resumo-card" title={EXPLICACAO.despesas_liquidas}>
                  <span className="resumo-card-rotulo">Despesas líquidas</span>
                  <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas, oculto)}</span>
                  {mesAnterior && (
                    <span className="resumo-card-delta">
                      {textoDelta(resumo.despesas_liquidas, mesAnterior.despesas_liquidas, oculto)}
                    </span>
                  )}
                </div>
              </>
            )}

            <div className="resumo-card" title={EXPLICACAO.reservas}>
              <span className="resumo-card-rotulo">Reservas</span>
              <span className="resumo-card-valor valor-investimento">{formatarMoeda(resumo.reservas, oculto)}</span>
              {mesAnterior && (
                <span className="resumo-card-delta">{textoDelta(resumo.reservas, mesAnterior.reservas, oculto)}</span>
              )}
            </div>
            <div className="resumo-card" title={EXPLICACAO.investimentos}>
              <span className="resumo-card-rotulo">Investimentos</span>
              <span className="resumo-card-valor valor-investimento">{formatarMoeda(resumo.investimentos, oculto)}</span>
              {mesAnterior && (
                <span className="resumo-card-delta">
                  {textoDelta(resumo.investimentos, mesAnterior.investimentos, oculto)}
                </span>
              )}
            </div>
            <div className="resumo-card" title={EXPLICACAO.taxa_poupanca}>
              <span className="resumo-card-rotulo">Taxa de poupança</span>
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
                          Parcela {c.parcela_atual} de {c.parcela_total} · {formatarData(c.data_compra)}
                        </span>
                      </div>
                      <span className="resumo-card-valor valor-despesa">{formatarMoeda(c.valor, oculto)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {evolucao && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Evolução Mensal</h2>
          <EvolucaoChart meses={evolucao.meses} />
        </div>
      )}

      {despesasCategoria && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Despesas por Categoria — {rotuloMesLongo(mesReferencia)}</h2>
          <DespesasPorCategoria dados={despesasCategoria} />
        </div>
      )}
    </div>
  )
}
