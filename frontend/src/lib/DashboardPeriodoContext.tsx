import { createContext, useContext, useState, type ReactNode } from 'react'
import { usePeriodo, type Periodo } from './periodo'

export type LeituraDashboard = 'caixa' | 'saude'

type DashboardPeriodoContextValue = Periodo & {
  leitura: LeituraDashboard
  setLeitura: (v: LeituraDashboard) => void
}

const DashboardPeriodoContext = createContext<DashboardPeriodoContextValue | null>(null)

/** Sobrevive à navegação — Dashboard perdia o período/mês selecionado (e o
 * toggle Leitura de Caixa/Saúde, bug reportado 2026-09-24) ao trocar de
 * tela e voltar (useState local, desmontado a cada troca de rota).
 * Instância própria, independente da de Gráficos (GraficosPeriodoContext)
 * — mudar o período no Dashboard não deve mudar o de Gráficos, são
 * leituras diferentes. Provider montado no AppShell, que fica montado o
 * tempo todo (só o <Outlet/> troca). */
export function DashboardPeriodoProvider({ children }: { children: ReactNode }) {
  const periodo = usePeriodo()
  const [leitura, setLeitura] = useState<LeituraDashboard>('saude')
  return (
    <DashboardPeriodoContext.Provider value={{ ...periodo, leitura, setLeitura }}>
      {children}
    </DashboardPeriodoContext.Provider>
  )
}

export function useDashboardPeriodo(): DashboardPeriodoContextValue {
  const context = useContext(DashboardPeriodoContext)
  if (!context) {
    throw new Error('useDashboardPeriodo precisa estar dentro de <DashboardPeriodoProvider>')
  }
  return context
}
