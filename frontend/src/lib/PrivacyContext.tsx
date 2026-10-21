import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

const CHAVE_STORAGE = 'financeapp:ocultar-valores'

type PrivacyContextValue = {
  oculto: boolean
  alternar: () => void
}

const PrivacyContext = createContext<PrivacyContextValue | null>(null)

export function PrivacyProvider({ children }: { children: ReactNode }) {
  const [oculto, setOculto] = useState(() => {
    try {
      return localStorage.getItem(CHAVE_STORAGE) === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(CHAVE_STORAGE, oculto ? '1' : '0')
    } catch {
      // localStorage indisponível (aba privada, storage bloqueado) — só não persiste entre sessões
    }
  }, [oculto])

  return (
    <PrivacyContext.Provider value={{ oculto, alternar: () => setOculto((v) => !v) }}>
      {children}
    </PrivacyContext.Provider>
  )
}

export function usePrivacidade(): PrivacyContextValue {
  const context = useContext(PrivacyContext)
  if (!context) {
    throw new Error('usePrivacidade precisa estar dentro de <PrivacyProvider>')
  }
  return context
}
