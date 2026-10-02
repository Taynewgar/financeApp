import { createContext, useContext, useState, type ReactNode } from 'react'
import { hojeAnoMes } from './periodo'

type PlanejamentoContextValue = {
  vigenciaMes: string
  setVigenciaMes: (v: string) => void
}

const PlanejamentoContext = createContext<PlanejamentoContextValue | null>(null)

/** Sobrevive à navegação — Planejamento perdia o mês selecionado ao trocar
 * de tela e voltar (useState local, desmontado a cada troca de rota).
 * Provider montado no AppShell, que fica montado o tempo todo. */
export function PlanejamentoProvider({ children }: { children: ReactNode }) {
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  return (
    <PlanejamentoContext.Provider value={{ vigenciaMes, setVigenciaMes }}>{children}</PlanejamentoContext.Provider>
  )
}

export function usePlanejamentoMes(): PlanejamentoContextValue {
  const context = useContext(PlanejamentoContext)
  if (!context) {
    throw new Error('usePlanejamentoMes precisa estar dentro de <PlanejamentoProvider>')
  }
  return context
}
