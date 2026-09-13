import { useEffect, useMemo, useState } from 'react'
import { EvolucaoChart } from '../components/EvolucaoChart'
import '../components/forms.css'
import '../components/resumoCards.css'
import '../components/crud.css'
import '../components/dashboard.css'
import { useAuth } from '../auth/AuthContext'
import { ApiError, apiFetch } from '../lib/api'
import { formatarData, formatarMoeda } from '../lib/formatar'
import type { CompromissoFuturo, EvolucaoMensal, ResumoMensal, SaldoCaixinha } from '../lib/types'

type Leitura = 'caixa' | 'saude'

const EXPLICACAO: Record<string, string> = {
  fluxo_caixa: 'Receitas menos despesas brutas (sem descontar estornos) — o que de fato entrou e saiu das contas.',
  receitas: 'Soma de todos os lançamentos do tipo Receita no mês.',
  despesas_brutas: 'Soma de todos os lançamentos do tipo Despesa no mês, antes de qualquer estorno/ressarcimento.',
  reservas: 'Aplicações menos retiradas em caixinhas e investimentos no mês (quanto a mais foi guardado).',
  resultado_saude: 'Resultado do mês (saúde financeira): receita mais ajustes soltos, menos despesas já líquidas dos estornos/ressarcimentos vinculados a elas.',
  receita_ajustada: 'Receitas mais estornos/ressarcimentos soltos (sem vínculo a uma despesa específica) — a base usada na leitura de saúde.',
  despesas_liquidas: 'Despesas menos estornos/ressarcimentos vinculados a elas — o quanto de fato saiu do bolso.',
  taxa_poupanca: 'Percentual da receita (já somando ajustes soltos) que sobrou depois das despesas líquidas.',
}

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

function classeResultado(valor: number): string {
  return valor >= 0 ? 'valor-receita' : 'valor-despesa'
}

function receitaAjustada(r: ResumoMensal): number {
  return r.receitas + r.ajustes_nao_vinculados
}

/** Variação percentual vs mês anterior, em texto neutro (a cor já está no
 * valor absoluto do card — a seta some ambiguidade de "melhorou ou piorou"
 * sem precisar saber, métrica a métrica, se subir é bom ou ruim). */
function textoDelta(atual: number, anterior: number): string {
  if (anterior === 0) {
    return atual === 0 ? 'Estável vs mês anterior' : `${atual > 0 ? '+' : ''}${formatarMoeda(atual)} vs mês anterior`
  }
  const variacao = ((atual - anterior) / Math.abs(anterior)) * 100
  if (Math.abs(variacao) < 0.05) return 'Estável vs mês anterior'
  const seta = variacao > 0 ? '↗' : '↘'
  return `${seta} ${Math.abs(variacao).toFixed(1)}% vs mês anterior`
}

export function Dashboard() {
  const { session } = useAuth()
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [leitura, setLeitura] = useState<Leitura>('saude')
  const [resumo, setResumo] = useState<ResumoMensal | null>(null)
  const [mesAnterior, setMesAnterior] = useState<ResumoMensal | null>(null)
  const [evolucao, setEvolucao] = useState<EvolucaoMensal | null>(null)
  const [caixinhas, setCaixinhas] = useState<SaldoCaixinha[] | null>(null)
  const [compromissos, setCompromissos] = useState<CompromissoFuturo[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    setErro(null)
    const inicioEvolucao = mesesAntes(vigenciaMes, 5) // janela de 6 meses (5 antes + o atual)
    Promise.all([
      apiFetch<ResumoMensal>(`/dashboard/mensal/${vigenciaMes}-01`),
      apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${inicioEvolucao}-01&fim=${vigenciaMes}-01`),
      apiFetch<SaldoCaixinha[]>(`/dashboard/patrimonio/${vigenciaMes}-01`),
    ])
      .then(([r, e, c]) => {
        setResumo(r)
        setEvolucao(e)
        setCaixinhas(c)
        // penúltimo ponto da janela de evolução é sempre o mês imediatamente
        // anterior ao selecionado (janela contígua, sem furos)
        setMesAnterior(e.meses.length >= 2 ? e.meses[e.meses.length - 2] : null)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o dashboard'))
  }, [vigenciaMes])

  // compromissos futuros não dependem do mês navegado (é sempre "a partir de hoje")
  useEffect(() => {
    apiFetch<CompromissoFuturo[]>('/dashboard/compromissos-futuros').then(setCompromissos).catch(() => setCompromissos([]))
  }, [])

  const reservasMes = useMemo(() => (resumo ? resumo.aplicacoes - resumo.retiradas : 0), [resumo])
  const reservasMesAnterior = useMemo(
    () => (mesAnterior ? mesAnterior.aplicacoes - mesAnterior.retiradas : 0),
    [mesAnterior],
  )

  const hero = resumo && (leitura === 'caixa' ? resumo.resultado_fluxo_caixa : resumo.resultado_saude)
  const heroAnterior =
    mesAnterior && (leitura === 'caixa' ? mesAnterior.resultado_fluxo_caixa : mesAnterior.resultado_saude)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: 22, marginTop: 0, marginBottom: 0 }}>Olá, {session?.user.email}</h1>
        <label className="campo" style={{ maxWidth: 180 }}>
          Mês
          <input type="month" value={vigenciaMes} onChange={(e) => setVigenciaMes(e.target.value)} max={hojeAnoMes()} />
        </label>
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
              {leitura === 'caixa' ? 'Resultado de caixa do mês' : 'Resultado de saúde do mês'}
            </span>
            <div className={classeResultado(hero ?? 0)} style={{ fontSize: 48, fontWeight: 600, lineHeight: 1.1 }}>
              {formatarMoeda(hero ?? 0)}
            </div>
            {heroAnterior !== null && heroAnterior !== undefined && (
              <span style={{ fontSize: 13, color: 'var(--cor-texto-suave)' }}>{textoDelta(hero ?? 0, heroAnterior)}</span>
            )}
          </div>

          {leitura === 'caixa' ? (
            <div className="resumo-cards">
              <div className="resumo-card" title={EXPLICACAO.receitas}>
                <span className="resumo-card-rotulo">Receitas</span>
                <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas)}</span>
                {mesAnterior && <span className="resumo-card-delta">{textoDelta(resumo.receitas, mesAnterior.receitas)}</span>}
              </div>
              <div className="resumo-card" title={EXPLICACAO.despesas_brutas}>
                <span className="resumo-card-rotulo">Despesas</span>
                <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_brutas)}</span>
                {mesAnterior && (
                  <span className="resumo-card-delta">{textoDelta(resumo.despesas_brutas, mesAnterior.despesas_brutas)}</span>
                )}
              </div>
              <div className="resumo-card" title={EXPLICACAO.reservas}>
                <span className="resumo-card-rotulo">Reservas no mês</span>
                <span className="resumo-card-valor valor-investimento">{formatarMoeda(reservasMes)}</span>
                {mesAnterior && <span className="resumo-card-delta">{textoDelta(reservasMes, reservasMesAnterior)}</span>}
              </div>
            </div>
          ) : (
            <div className="resumo-cards">
              <div className="resumo-card" title={EXPLICACAO.receita_ajustada}>
                <span className="resumo-card-rotulo">Receita ajustada</span>
                <span className="resumo-card-valor valor-receita">{formatarMoeda(receitaAjustada(resumo))}</span>
                {mesAnterior && (
                  <span className="resumo-card-delta">
                    {textoDelta(receitaAjustada(resumo), receitaAjustada(mesAnterior))}
                  </span>
                )}
              </div>
              <div className="resumo-card" title={EXPLICACAO.despesas_liquidas}>
                <span className="resumo-card-rotulo">Despesas líquidas</span>
                <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas)}</span>
                {mesAnterior && (
                  <span className="resumo-card-delta">
                    {textoDelta(resumo.despesas_liquidas, mesAnterior.despesas_liquidas)}
                  </span>
                )}
              </div>
              <div className="resumo-card" title={EXPLICACAO.taxa_poupanca}>
                <span className="resumo-card-rotulo">Taxa de poupança</span>
                <span className="resumo-card-valor">
                  {resumo.taxa_poupanca === null ? '—' : `${resumo.taxa_poupanca.toFixed(1)}%`}
                </span>
                {mesAnterior && resumo.taxa_poupanca !== null && mesAnterior.taxa_poupanca !== null && (
                  <span className="resumo-card-delta">{textoDelta(resumo.taxa_poupanca, mesAnterior.taxa_poupanca)}</span>
                )}
              </div>
            </div>
          )}
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
                      <span className="resumo-card-valor valor-investimento">{formatarMoeda(c.saldo)}</span>
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
                      <span className="resumo-card-valor valor-despesa">{formatarMoeda(c.valor)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {evolucao && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Evolução (últimos 6 meses)</h2>
          <EvolucaoChart meses={evolucao.meses} />
        </div>
      )}
    </div>
  )
}
