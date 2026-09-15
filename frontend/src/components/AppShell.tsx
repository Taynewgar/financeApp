import { useEffect, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { checkHealth } from '../lib/api'
import './AppShell.css'

type StatusBackend = 'ocioso' | 'aguardando' | 'falhou'

const SECOES = [
  { to: '/dashboard', label: 'Dashboard', icone: '◧' },
  { to: '/lancamentos', label: 'Lançamentos', icone: '⌕' },
  { to: '/planejamento', label: 'Planejamento', icone: '▤' },
  { to: '/estruturas-de-custo', label: 'Estruturas de Custo', icone: '≣' },
  { to: '/configuracoes', label: 'Configurações', icone: '⚙' },
]

function linkClasse(base: string) {
  return ({ isActive }: { isActive: boolean }) => `${base}${isActive ? ' ativo' : ''}`
}

export function AppShell({ children }: { children?: ReactNode }) {
  const { session, signOut } = useAuth()

  const [statusBackend, setStatusBackend] = useState<StatusBackend>('ocioso')
  const [segundosEspera, setSegundosEspera] = useState(0)
  const [tentativa, setTentativa] = useState(0)

  // dispara assim que o usuário entra no app — se o backend estiver
  // "dormindo" (plano free do Render hiberna após inatividade), começa a
  // acordar aqui em vez de só quando a primeira tela pedir dados de verdade.
  // Só mostra o aviso se demorar mais que o normal (evita "piscar" banner
  // em toda navegação quando o backend já está acordado).
  useEffect(() => {
    let cancelado = false
    let resolvido = false
    let intervaloContador: ReturnType<typeof setInterval> | undefined
    const inicio = Date.now()

    const timerMostrarAviso = setTimeout(() => {
      if (cancelado || resolvido) return
      setStatusBackend('aguardando')
      intervaloContador = setInterval(() => {
        setSegundosEspera(Math.floor((Date.now() - inicio) / 1000))
      }, 1000)
    }, 1500)

    checkHealth()
      .then(() => {
        resolvido = true
        if (!cancelado) setStatusBackend('ocioso')
      })
      .catch(() => {
        resolvido = true
        if (!cancelado) setStatusBackend('falhou')
      })
      .finally(() => {
        clearTimeout(timerMostrarAviso)
        if (intervaloContador) clearInterval(intervaloContador)
      })

    return () => {
      cancelado = true
      clearTimeout(timerMostrarAviso)
      if (intervaloContador) clearInterval(intervaloContador)
    }
  }, [tentativa])

  return (
    <div className="shell-raiz">
      {statusBackend !== 'ocioso' && (
        <div className={`shell-banner-backend${statusBackend === 'falhou' ? ' falhou' : ''}`} role="status">
          {statusBackend === 'aguardando' ? (
            <span>
              Conectando ao servidor… ele pode estar "acordando" após um tempo sem uso (plano gratuito) — até ~50s na
              primeira vez. Aguardando há {segundosEspera}s.
            </span>
          ) : (
            <span>
              Não foi possível conectar ao servidor.{' '}
              <button type="button" onClick={() => setTentativa((n) => n + 1)}>
                Tentar novamente
              </button>
            </span>
          )}
        </div>
      )}

      <div className="shell">
        <nav className="shell-nav" aria-label="Navegação principal">
          <div className="shell-nav-header">Finance App</div>
          {SECOES.map((secao) => (
            <NavLink key={secao.to} to={secao.to} className={linkClasse('shell-nav-link')}>
              {secao.icone} &nbsp;{secao.label}
            </NavLink>
          ))}
          <div className="shell-nav-footer">
            <span>{session?.user.email}</span>
            <button type="button" className="shell-sair" onClick={() => signOut()}>
              Sair
            </button>
          </div>
        </nav>

        <main className="shell-conteudo">{children ?? <Outlet />}</main>

        <Link to="/lancamentos/novo" className="shell-fab" aria-label="Novo lançamento" title="Novo lançamento">
          +
        </Link>

        <nav className="shell-bottom-nav" aria-label="Navegação principal (mobile)">
          {SECOES.map((secao) => (
            <NavLink key={secao.to} to={secao.to} className={linkClasse('shell-bottom-nav-link')}>
              <span aria-hidden="true">{secao.icone}</span>
              {secao.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
