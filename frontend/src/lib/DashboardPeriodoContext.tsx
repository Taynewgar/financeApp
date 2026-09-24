import { createContext, useContext, type ReactNode } from 'react'
import { usePeriodo, type Periodo } from './periodo'

const DashboardPeriodoContext = createContext<Periodo | null>(null)

/** Sobrevive à navegação — Dashboard perdia o período/mês selecionado ao
 * trocar de tela e voltar (useState local, desmontado a cada troca de
 * rota). Instância própria, independente da de Gráficos (GraficosPeriodo
 * Context) — mudar o período no Dashboard não deve mudar o de Gráficos,
 * são leituras diferentes. Provider montado no AppShell, que fica
 * montado o tempo todo (só o <Outlet/> troca). */
export function DashboardPeriodoProvider({ children }: { children: ReactNode }) {
  const periodo = usePeriodo()
  return <DashboardPeriodoContext.Provider value={periodo}>{children}</DashboardPeriodoContext.Provider>
}

export function useDashboardPeriodo(): Periodo {
  const context = useContext(DashboardPeriodoContext)
  if (!context) {
    throw new Error('useDashboardPeriodo precisa estar dentro de <DashboardPeriodoProvider>')
  }
  return context
}
