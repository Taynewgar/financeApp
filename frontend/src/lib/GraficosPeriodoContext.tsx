import { createContext, useContext, type ReactNode } from 'react'
import { usePeriodo, type Periodo } from './periodo'

const GraficosPeriodoContext = createContext<Periodo | null>(null)

/** Sobrevive à navegação — Gráficos perdia o período/mês selecionado ao
 * trocar de tela e voltar, porque o estado vivia num useState local do
 * componente (desmontado a cada troca de rota). Provider montado no
 * AppShell, que fica montado o tempo todo (só o <Outlet/> troca). */
export function GraficosPeriodoProvider({ children }: { children: ReactNode }) {
  const periodo = usePeriodo()
  return <GraficosPeriodoContext.Provider value={periodo}>{children}</GraficosPeriodoContext.Provider>
}

export function useGraficosPeriodo(): Periodo {
  const context = useContext(GraficosPeriodoContext)
  if (!context) {
    throw new Error('useGraficosPeriodo precisa estar dentro de <GraficosPeriodoProvider>')
  }
  return context
}
