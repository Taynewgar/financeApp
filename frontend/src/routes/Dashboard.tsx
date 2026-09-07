import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { checkHealth } from '../lib/api'

type StatusBackend = 'verificando' | 'online' | 'offline'

export function Dashboard() {
  const { session } = useAuth()
  const [status, setStatus] = useState<StatusBackend>('verificando')

  useEffect(() => {
    let ativo = true
    checkHealth()
      .then(() => ativo && setStatus('online'))
      .catch(() => ativo && setStatus('offline'))
    return () => {
      ativo = false
    }
  }, [])

  return (
    <div>
      <h1 style={{ fontSize: 22, marginTop: 0 }}>Olá, {session?.user.email}</h1>
      <p style={{ color: 'var(--cor-texto-suave)' }}>
        Backend:{' '}
        {status === 'verificando' && 'verificando…'}
        {status === 'online' && <span style={{ color: 'var(--cor-sucesso)' }}>conectado</span>}
        {status === 'offline' && (
          <span style={{ color: 'var(--cor-perigo)' }}>
            indisponível — confira VITE_API_BASE_URL no .env.local
          </span>
        )}
      </p>
      <p style={{ color: 'var(--cor-texto-suave)' }}>
        Resumo mensal, gráficos e KPIs chegam numa próxima entrega — esta tela por enquanto só confirma que login e
        conexão com a API estão funcionando.
      </p>
    </div>
  )
}
