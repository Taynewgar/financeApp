import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function Login() {
  const { session, signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  if (session) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setErro(null)
    setEnviando(true)
    const { error } = await signIn(email, password)
    setEnviando(false)
    if (error) {
      setErro('E-mail ou senha inválidos.')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: '100%',
          maxWidth: 360,
          background: 'var(--cor-superficie)',
          border: '1px solid var(--cor-borda)',
          borderRadius: 'var(--raio)',
          boxShadow: 'var(--sombra)',
          padding: 32,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>Finance App</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--cor-texto-suave)', fontSize: 14 }}>
            Entre com sua conta para continuar
          </p>
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
          E-mail
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={campoEstilo}
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
          Senha
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={campoEstilo}
          />
        </label>

        {erro && (
          <p role="alert" style={{ color: 'var(--cor-perigo)', fontSize: 14, margin: 0 }}>
            {erro}
          </p>
        )}

        <button type="submit" disabled={enviando} style={botaoEstilo}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

const campoEstilo: React.CSSProperties = {
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid var(--cor-borda)',
  background: 'var(--cor-fundo)',
  color: 'var(--cor-texto)',
}

const botaoEstilo: React.CSSProperties = {
  marginTop: 8,
  padding: '10px 16px',
  borderRadius: 8,
  border: 'none',
  background: 'var(--cor-acento)',
  color: 'var(--cor-acento-texto)',
  fontWeight: 600,
  cursor: 'pointer',
}
