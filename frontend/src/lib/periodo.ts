import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from './api'
import type { PrimeiroMes } from './types'

export type ModoData = 'mes' | 'intervalo' | 'todos'
export type BaseMedia = 'ate_mes' | 'todos_meses'

const MESES_NOME = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]

export function hojeAnoMes(): string {
  return new Date().toISOString().slice(0, 7)
}

/** 'YYYY-MM' menos N meses, sempre 'YYYY-MM' de volta. */
export function mesesAntes(anoMes: string, n: number): string {
  const [ano, mes] = anoMes.split('-').map(Number)
  const totalMeses = ano * 12 + (mes - 1) - n
  const anoResultado = Math.floor(totalMeses / 12)
  const mesResultado = (totalMeses % 12) + 1
  return `${anoResultado}-${String(mesResultado).padStart(2, '0')}`
}

export function rotuloMesLongo(anoMes: string): string {
  const [ano, mes] = anoMes.split('-').map(Number)
  return `${MESES_NOME[mes - 1]} de ${ano}`
}

/** Estado + derivação do seletor Mês/Intervalo/Todos os meses — reaproveitado
 * pelo Dashboard e pela tela de Gráficos (mesmo componente, não um 3º
 * modelo de filtro), ver docs/backlog.md item 5. */
export function usePeriodo() {
  const [modoData, setModoData] = useState<ModoData>('mes')
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  const [intervaloInicio, setIntervaloInicio] = useState(mesesAntes(hojeAnoMes(), 2))
  const [intervaloFim, setIntervaloFim] = useState(hojeAnoMes())
  const [baseMedia, setBaseMedia] = useState<BaseMedia>('ate_mes')
  const [primeiroMes, setPrimeiroMes] = useState<string | null>(null)

  // "Todos os meses" precisa saber onde o histórico começa
  useEffect(() => {
    apiFetch<PrimeiroMes>('/dashboard/primeiro-mes')
      .then((p) => setPrimeiroMes(p.vigencia_mes ? p.vigencia_mes.slice(0, 7) : hojeAnoMes()))
      .catch(() => setPrimeiroMes(hojeAnoMes()))
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

  return {
    modoData, setModoData,
    vigenciaMes, setVigenciaMes,
    intervaloInicio, setIntervaloInicio,
    intervaloFim, setIntervaloFim,
    baseMedia, setBaseMedia,
    primeiroMes,
    periodoInicio, periodoFim, mesReferencia,
  }
}

export type Periodo = ReturnType<typeof usePeriodo>

/** "Até o mês": média só dos meses com valor lançado (exclui mês vazio, seja
 * passado sem lançamento ou futuro ainda não navegado). "Ritmo anual": soma
 * ÷ pelo total de meses do período, incluindo os vazios — mostra o ritmo em
 * relação ao período cheio, não "quanto é o mês típico". */
export function media(valores: number[], baseMedia: BaseMedia): number {
  const relevantes = baseMedia === 'ate_mes' ? valores.filter((v) => v !== 0) : valores
  return relevantes.length ? relevantes.reduce((soma, v) => soma + v, 0) / relevantes.length : 0
}
