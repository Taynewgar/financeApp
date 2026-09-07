import { useEffect, type ReactNode } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { checkHealth } from '../lib/api'
import './AppShell.css'

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

  // dispara assim que o usuário entra no app — se o backend estiver
  // "dormindo" (plano free do Render hiberna após inatividade), começa a
  // acordar aqui em vez de só quando a primeira tela pedir dados de verdade
  useEffect(() => {
    checkHealth().catch(() => {})
  }, [])

  return (
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
  )
}
