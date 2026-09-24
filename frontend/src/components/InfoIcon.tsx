import './infoIcon.css'

/** Sinalizador visual de "isto tem uma explicação extra no hover" — o
 * tooltip em si continua sendo o `title` nativo do elemento pai; este
 * ícone só avisa que ele existe (sem ele, só se descobre passando o
 * mouse por acaso). Decorativo: a explicação acessível já vem do
 * `title` do elemento pai, então fica fora da árvore de acessibilidade. */
export function InfoIcon() {
  return (
    <span className="info-icone" aria-hidden="true">
      ?
    </span>
  )
}
