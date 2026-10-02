import { createContext, useContext, useState, type ReactNode } from 'react'
import type { EstruturaCusto, MeioPagamento, TipoMovimento } from './types'

export type Filtros = {
  tipoMovimento: TipoMovimento | ''
  categoriaId: string
  subcategoriaId: string
  contaId: string
  caixinhaId: string
  estruturaCusto: EstruturaCusto | ''
  meioPagamento: MeioPagamento | ''
  dataInicio: string
  dataFim: string
  descricao: string
}

export const FILTROS_VAZIOS: Filtros = {
  tipoMovimento: '',
  categoriaId: '',
  subcategoriaId: '',
  contaId: '',
  caixinhaId: '',
  estruturaCusto: '',
  meioPagamento: '',
  dataInicio: '',
  dataFim: '',
  descricao: '',
}

type LancamentosFiltrosContextValue = {
  filtros: Filtros
  setFiltros: (f: Filtros | ((atual: Filtros) => Filtros)) => void
  mesRapido: string
  setMesRapido: (m: string) => void
  anoRapido: string
  setAnoRapido: (a: string) => void
}

const LancamentosFiltrosContext = createContext<LancamentosFiltrosContextValue | null>(null)

/** Sobrevive à navegação — filtros de Lançamentos resetavam ao ir pra
 * outra tela e voltar (useState local, desmontado a cada troca de rota).
 * Provider montado no AppShell, que fica montado o tempo todo. */
export function LancamentosFiltrosProvider({ children }: { children: ReactNode }) {
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_VAZIOS)
  const [mesRapido, setMesRapido] = useState('')
  const [anoRapido, setAnoRapido] = useState(String(new Date().getFullYear()))

  return (
    <LancamentosFiltrosContext.Provider value={{ filtros, setFiltros, mesRapido, setMesRapido, anoRapido, setAnoRapido }}>
      {children}
    </LancamentosFiltrosContext.Provider>
  )
}

export function useLancamentosFiltros(): LancamentosFiltrosContextValue {
  const context = useContext(LancamentosFiltrosContext)
  if (!context) {
    throw new Error('useLancamentosFiltros precisa estar dentro de <LancamentosFiltrosProvider>')
  }
  return context
}
