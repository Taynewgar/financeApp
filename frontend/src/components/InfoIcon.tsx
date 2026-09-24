import { useEffect, useRef, useState } from 'react'
import './infoIcon.css'

/** Sinalizador + acesso à explicação extra de um rótulo. Clicável em vez
 * de depender só de `title`/hover — em touchscreen não existe hover, então
 * um tooltip nativo nunca aparece no toque (bug reportado 2026-09-24). O
 * clique funciona igual em mobile e desktop, sem depender do navegador. */
export function InfoIcon({ texto }: { texto: string }) {
  const [aberto, setAberto] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!aberto) return
    function fecharSeFora(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setAberto(false)
    }
    function fecharNoEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setAberto(false)
    }
    document.addEventListener('mousedown', fecharSeFora)
    document.addEventListener('keydown', fecharNoEscape)
    return () => {
      document.removeEventListener('mousedown', fecharSeFora)
      document.removeEventListener('keydown', fecharNoEscape)
    }
  }, [aberto])

  return (
    <span className="info-icone-wrap" ref={ref}>
      <button
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
      {aberto && (
        <span role="tooltip" className="info-icone-balao">
          {texto}
        </span>
      )}
    </span>
  )
}
