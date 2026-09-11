import { useEffect, useMemo, useState } from 'react'
import { EvolucaoChart } from '../components/EvolucaoChart'
import '../components/forms.css'
import '../components/resumoCards.css'
import { useAuth } from '../auth/AuthContext'
import { ApiError, apiFetch } from '../lib/api'
import { formatarMoeda } from '../lib/formatar'
import type { EvolucaoMensal, ResumoMensal } from '../lib/types'

const EXPLICACAO: Record<string, string> = {
  resultado: 'Resultado do mês (saúde financeira): receita mais ajustes soltos, menos despesas já líquidas dos estornos/ressarcimentos vinculados a elas.',
  receitas: 'Soma de todos os lançamentos do tipo Receita no mês.',
  despesas_liquidas: 'Despesas menos estornos/ressarcimentos vinculados a elas — o quanto de fato saiu do bolso.',
  fluxo_caixa: 'Receitas menos despesas brutas (sem descontar estornos) — o que de fato entrou e saiu das contas.',
  taxa_poupanca: 'Percentual da receita (já somando ajustes soltos) que sobrou depois das despesas líquidas.',
  reservas: 'Aplicações menos retiradas em caixinhas e investimentos no mês (quanto a mais foi guardado).',
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

export function Dashboard() {
  const { session } = useAuth()
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [resumo, setResumo] = useState<ResumoMensal | null>(null)
  const [evolucao, setEvolucao] = useState<EvolucaoMensal | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    setErro(null)
    const inicioEvolucao = mesesAntes(vigenciaMes, 5) // janela de 6 meses (5 antes + o atual)
    Promise.all([
      apiFetch<ResumoMensal>(`/dashboard/mensal/${vigenciaMes}-01`),
      apiFetch<EvolucaoMensal>(`/dashboard/evolucao?inicio=${inicioEvolucao}-01&fim=${vigenciaMes}-01`),
    ])
      .then(([r, e]) => {
        setResumo(r)
        setEvolucao(e)
      })
      .catch((e) => setErro(e instanceof ApiError ? e.message : 'Falha ao carregar o dashboard'))
  }, [vigenciaMes])

  const reservasMes = useMemo(() => (resumo ? resumo.aplicacoes - resumo.retiradas : 0), [resumo])

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
          <div title={EXPLICACAO.resultado} style={{ margin: '20px 0' }}>
            <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>Resultado do mês</span>
            <div className={classeResultado(resumo.resultado_saude)} style={{ fontSize: 48, fontWeight: 600, lineHeight: 1.1 }}>
              {formatarMoeda(resumo.resultado_saude)}
            </div>
          </div>

          <div className="resumo-cards">
            <div className="resumo-card" title={EXPLICACAO.receitas}>
              <span className="resumo-card-rotulo">Receitas</span>
              <span className="resumo-card-valor valor-receita">{formatarMoeda(resumo.receitas)}</span>
            </div>
            <div className="resumo-card" title={EXPLICACAO.despesas_liquidas}>
              <span className="resumo-card-rotulo">Despesas líquidas</span>
              <span className="resumo-card-valor valor-despesa">{formatarMoeda(resumo.despesas_liquidas)}</span>
            </div>
            <div className="resumo-card" title={EXPLICACAO.fluxo_caixa}>
              <span className="resumo-card-rotulo">Fluxo de caixa</span>
              <span className={`resumo-card-valor ${classeResultado(resumo.resultado_fluxo_caixa)}`}>
                {formatarMoeda(resumo.resultado_fluxo_caixa)}
              </span>
            </div>
            <div className="resumo-card" title={EXPLICACAO.taxa_poupanca}>
              <span className="resumo-card-rotulo">Taxa de poupança</span>
              <span className="resumo-card-valor">
                {resumo.taxa_poupanca === null ? '—' : `${resumo.taxa_poupanca.toFixed(1)}%`}
              </span>
            </div>
            <div className="resumo-card" title={EXPLICACAO.reservas}>
              <span className="resumo-card-rotulo">Reservas no mês</span>
              <span className="resumo-card-valor valor-investimento">{formatarMoeda(reservasMes)}</span>
            </div>
          </div>
        </>
      )}

      {resumo === null && !erro && <p>Carregando…</p>}

      {evolucao && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>Evolução (últimos 6 meses)</h2>
          <EvolucaoChart meses={evolucao.meses} />
        </div>
      )}
    </div>
  )
}
