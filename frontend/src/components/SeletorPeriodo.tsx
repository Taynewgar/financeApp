import './dashboard.css'
import { InfoIcon } from './InfoIcon'
import { hojeAnoMes, rotuloMesLongo, type Periodo } from '../lib/periodo'

const EXPLICACAO_BASE_MEDIA =
  '"Até o mês": média só dos meses que já têm lançamento no período. "Ritmo anual": soma do período ÷ 12 sempre — mostra o ritmo em relação a um ano cheio, não "quanto é o mês típico".'

/** Mês / Intervalo / Todos os meses + Base da média — mesmo seletor
 * reaproveitado pelo Dashboard e pela tela de Gráficos (ver usePeriodo).
 * `mostrarBaseMedia` fica desligado no Dashboard (nenhum KPI lá consome
 * baseMedia — os gráficos que consomem migraram pra Gráficos). */
export function SeletorPeriodo(periodo: Periodo & { mostrarBaseMedia?: boolean }) {
  const {
    modoData, setModoData,
    vigenciaMes, setVigenciaMes,
    intervaloInicio, setIntervaloInicio,
    intervaloFim, setIntervaloFim,
    baseMedia, setBaseMedia,
    primeiroMes,
    mostrarBaseMedia = true,
  } = periodo

  return (
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

      {mostrarBaseMedia && (
        <div className="campo">
          <span style={{ fontSize: 12, color: 'var(--cor-texto-suave)' }}>
            Base da média
            <InfoIcon texto={EXPLICACAO_BASE_MEDIA} />
          </span>
          <div className="segmentado">
            <button type="button" className={baseMedia === 'ate_mes' ? 'ativo' : ''} onClick={() => setBaseMedia('ate_mes')}>
              Até o mês
            </button>
            <button
              type="button"
              className={baseMedia === 'todos_meses' ? 'ativo' : ''}
              onClick={() => setBaseMedia('todos_meses')}
            >
              Ritmo anual
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
