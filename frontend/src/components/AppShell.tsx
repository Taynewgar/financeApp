import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { checkHealth } from '../lib/api'
import { DashboardPeriodoProvider } from '../lib/DashboardPeriodoContext'
import { EstruturaCustoProvider } from '../lib/EstruturaCustoContext'
import { GraficosPeriodoProvider } from '../lib/GraficosPeriodoContext'
import { LancamentosFiltrosProvider } from '../lib/LancamentosFiltrosContext'
import { PlanejamentoProvider } from '../lib/PlanejamentoContext'
import { itemMaisUsadoMenuMobile, registrarUsoMenuMobile } from '../lib/usoMenuMobile'
import { BotaoPrivacidade } from './BotaoPrivacidade'
import './AppShell.css'

type StatusBackend = 'ocioso' | 'aguardando' | 'falhou'

const SECOES = [
  { to: '/dashboard', label: 'Dashboard', icone: '◧' },
  { to: '/lancamentos', label: 'Lançamentos', icone: '⌕' },
  { to: '/planejamento', label: 'Planejamento', icone: '▤' },
  { to: '/estruturas-de-custo', label: 'Estruturas de Custo', icone: '≣' },
  { to: '/graficos', label: 'Gráficos', icone: '◔' },
  { to: '/configuracoes', label: 'Configurações', icone: '⚙' },
]

// barra inferior mobile: só as 4 mais usadas ficam diretas (decisão do
// usuário, item 21 do backlog) — o resto mora no menu "•••", agrupado por
// seção pra crescer bem conforme mais telas entrarem aqui.
const SECOES_BARRA_MOBILE = [
  { to: '/dashboard', label: 'Dashboard', icone: '◧' },
  { to: '/lancamentos', label: 'Lançamentos', icone: '⌕' },
  { to: '/estruturas-de-custo', label: 'Estruturas', icone: '≣' },
  { to: '/graficos', label: 'Gráficos', icone: '◔' },
]

const SECOES_MENU_MOBILE = [
  { grupo: 'Planejamento', to: '/planejamento', label: 'Planejamento', icone: '▤' },
  { grupo: 'Conta', to: '/configuracoes', label: 'Configurações', icone: '⚙' },
]

function linkClasse(base: string) {
  return ({ isActive }: { isActive: boolean }) => `${base}${isActive ? ' ativo' : ''}`
}

export function AppShell({ children }: { children?: ReactNode }) {
  const { session, signOut } = useAuth()
  const location = useLocation()

  const [statusBackend, setStatusBackend] = useState<StatusBackend>('ocioso')
  const [segundosEspera, setSegundosEspera] = useState(0)
  const [tentativa, setTentativa] = useState(0)
  const [menuMobileAberto, setMenuMobileAberto] = useState(false)
  const [usoRegistrado, setUsoRegistrado] = useState(0)

  // AppShell não desmonta ao navegar (só o <Outlet/> troca) — sem isso o
  // menu ficaria aberto por cima da tela seguinte depois de tocar num item.
  useEffect(() => {
    setMenuMobileAberto(false)

    // item 29 do backlog: cada visita a uma rota que vive dentro do menu
    // "mais" conta pro contador de uso (localStorage) que decide se ela
    // vira atalho de destaque no topo da sheet.
    const secaoVisitada = SECOES_MENU_MOBILE.find((secao) => location.pathname.startsWith(secao.to))
    if (secaoVisitada) {
      registrarUsoMenuMobile(secaoVisitada.to)
      setUsoRegistrado((n) => n + 1)
    }
  }, [location.pathname])

  const menuMobileAtivo =
    menuMobileAberto || SECOES_MENU_MOBILE.some((secao) => location.pathname.startsWith(secao.to))

  // usoRegistrado não é usado no corpo — só existe pra invalidar este memo
  // quando o contador de uso muda (ele mesmo mora em localStorage, fora do
  // ciclo de re-render normal do React).
  const itemDestaqueMenuMobile = useMemo(
    () => itemMaisUsadoMenuMobile(SECOES_MENU_MOBILE),
    [usoRegistrado], // eslint-disable-line react-hooks/exhaustive-deps
  )

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

      <div className="shell-topo-mobile">
        <span>Finance App</span>
        <BotaoPrivacidade />
      </div>

      <div className="shell">
        <nav className="shell-nav" aria-label="Navegação principal">
          <div className="shell-nav-header shell-nav-header-linha">
            <span>Finance App</span>
            <BotaoPrivacidade />
          </div>
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

        <main className="shell-conteudo">
          <DashboardPeriodoProvider>
            <LancamentosFiltrosProvider>
              <GraficosPeriodoProvider>
                <EstruturaCustoProvider>
                  <PlanejamentoProvider>{children ?? <Outlet />}</PlanejamentoProvider>
                </EstruturaCustoProvider>
              </GraficosPeriodoProvider>
            </LancamentosFiltrosProvider>
          </DashboardPeriodoProvider>
        </main>

        <Link
          to="/lancamentos/novo"
          className={`shell-fab${menuMobileAberto ? ' escondido' : ''}`}
          aria-label="Novo lançamento"
          title="Novo lançamento"
        >
          +
        </Link>

        {menuMobileAberto && <div className="shell-menu-backdrop" onClick={() => setMenuMobileAberto(false)} />}

        {menuMobileAberto && (
          <div className="shell-menu-sheet" role="dialog" aria-label="Menu">
            <div className="shell-menu-sheet-handle" />
            <div className="shell-menu-sheet-header">
              <span>Menu</span>
              <button type="button" onClick={() => setMenuMobileAberto(false)} aria-label="Fechar menu">
                ✕
              </button>
            </div>
            <div className="shell-menu-sheet-lista">
              {itemDestaqueMenuMobile && (
                <div className="shell-menu-sheet-destaque">
                  <div className="shell-menu-sheet-grupo-titulo">Mais usado</div>
                  <Link to={itemDestaqueMenuMobile.to} className="shell-menu-sheet-item">
                    <span aria-hidden="true">{itemDestaqueMenuMobile.icone}</span>
                    {itemDestaqueMenuMobile.label}
                  </Link>
                </div>
              )}
              {SECOES_MENU_MOBILE.map((secao) => (
                <div key={secao.to} className="shell-menu-sheet-grupo">
                  <div className="shell-menu-sheet-grupo-titulo">{secao.grupo}</div>
                  <Link to={secao.to} className="shell-menu-sheet-item">
                    <span aria-hidden="true">{secao.icone}</span>
                    {secao.label}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        <nav className="shell-bottom-nav" aria-label="Navegação principal (mobile)">
          {SECOES_BARRA_MOBILE.map((secao) => (
            <NavLink key={secao.to} to={secao.to} className={linkClasse('shell-bottom-nav-link')}>
              <span aria-hidden="true">{secao.icone}</span>
              {secao.label}
            </NavLink>
          ))}
          <div className="shell-bottom-nav-divisor" aria-hidden="true" />
          <button
            type="button"
            onClick={() => setMenuMobileAberto((aberto) => !aberto)}
            className={`shell-bottom-nav-link shell-bottom-nav-menu${menuMobileAtivo ? ' ativo' : ''}`}
            aria-expanded={menuMobileAberto}
            aria-haspopup="true"
          >
            <span aria-hidden="true">{menuMobileAberto ? '✕' : '•••'}</span>
            Menu
          </button>
        </nav>
      </div>
    </div>
  )
}
