import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import './infoIcon.css'

const MARGEM_VIEWPORT = 8
// altura estimada de um balão curto (2-3 linhas de texto + padding) — boa o
// bastante pra decidir se cabe embaixo do ícone sem esperar o navegador
// desenhar; os textos reais de InfoIcon nunca passam disso na prática.
const ALTURA_BALAO_ESTIMADA = 90

type Posicao = { top: number; left: number }

/** Sinalizador + acesso à explicação extra de um rótulo. Clicável em vez
 * de depender só de `title`/hover — em touchscreen não existe hover, então
 * um tooltip nativo nunca aparece no toque (bug reportado 2026-09-24). O
 * clique funciona igual em mobile e desktop, sem depender do navegador.
 *
 * O balão é `position: fixed` com coordenadas calculadas a partir do
 * ícone (não `position: absolute` ancorado nele) — perto das bordas do
 * viewport (item 19 do backlog, reportado 2026-09-24), um balão absoluto
 * podia extrapolar a tela e ampliar a área rolável da página; fixed não
 * conta pra altura/largura do documento, e a posição é clampada dentro do
 * viewport (com flip pra cima quando não cabe embaixo). */
export function InfoIcon({ texto }: { texto: string }) {
  const [aberto, setAberto] = useState(false)
  const [posicao, setPosicao] = useState<Posicao | null>(null)
  const ref = useRef<HTMLSpanElement>(null)
  const botaoRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!aberto) return
    function fecharSeFora(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setAberto(false)
    }
    function fecharNoEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setAberto(false)
    }
    function fecharAoRolar() {
      // um balão fixed fica "grudado" no lugar errado assim que a página
      // (ou qualquer container rolável ancestral) rola — fecha em vez de
      // deixar desalinhado do ícone; capture:true pega scroll de dentro
      // de qualquer container, não só da window.
      setAberto(false)
    }
    document.addEventListener('mousedown', fecharSeFora)
    document.addEventListener('keydown', fecharNoEscape)
    window.addEventListener('scroll', fecharAoRolar, true)
    return () => {
      document.removeEventListener('mousedown', fecharSeFora)
      document.removeEventListener('keydown', fecharNoEscape)
      window.removeEventListener('scroll', fecharAoRolar, true)
    }
  }, [aberto])

  useLayoutEffect(() => {
    if (!aberto || !botaoRef.current) {
      setPosicao(null)
      return
    }
    const rectBotao = botaoRef.current.getBoundingClientRect()
    const larguraBalao = Math.min(260, window.innerWidth - MARGEM_VIEWPORT * 2)

    let left = rectBotao.left
    left = Math.min(left, window.innerWidth - larguraBalao - MARGEM_VIEWPORT)
    left = Math.max(left, MARGEM_VIEWPORT)

    let top = rectBotao.bottom + 6
    if (top + ALTURA_BALAO_ESTIMADA > window.innerHeight - MARGEM_VIEWPORT) {
      // não cabe embaixo do ícone — abre em cima dele
      top = Math.max(MARGEM_VIEWPORT, rectBotao.top - ALTURA_BALAO_ESTIMADA - 6)
    }
    setPosicao({ top, left })
  }, [aberto])

  return (
    <span className="info-icone-wrap" ref={ref}>
      <button
        ref={botaoRef}
        type="button"
        className="info-icone"
        aria-expanded={aberto}
        aria-label="Mais informações"
        onClick={(e) => {
          e.stopPropagation()
          setAberto((v) => !v)
        }}
      >
        ?
      </button>
      {aberto && posicao && (
        <span role="tooltip" className="info-icone-balao" style={{ top: posicao.top, left: posicao.left }}>
          {texto}
        </span>
      )}
    </span>
  )
}
