import { createContext, useContext, useState, type ReactNode } from 'react'
import { hojeAnoMes } from './periodo'

type EstruturaCustoContextValue = {
  vigenciaMes: string
  setVigenciaMes: (v: string) => void
}

const EstruturaCustoContext = createContext<EstruturaCustoContextValue | null>(null)

/** Sobrevive à navegação — Estrutura de Custo perdia o mês selecionado ao
 * trocar de tela e voltar (useState local, desmontado a cada troca de
 * rota). Provider montado no AppShell, que fica montado o tempo todo. */
export function EstruturaCustoProvider({ children }: { children: ReactNode }) {
  const [vigenciaMes, setVigenciaMes] = useState(hojeAnoMes())
  return (
    <EstruturaCustoContext.Provider value={{ vigenciaMes, setVigenciaMes }}>{children}</EstruturaCustoContext.Provider>
  )
}

export function useEstruturaCustoMes(): EstruturaCustoContextValue {
  const context = useContext(EstruturaCustoContext)
  if (!context) {
    throw new Error('useEstruturaCustoMes precisa estar dentro de <EstruturaCustoProvider>')
  }
  return context
}
