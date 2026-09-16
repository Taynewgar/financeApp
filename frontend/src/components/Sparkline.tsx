import './sparkline.css'

/** Forma pura dos últimos meses — sem eixo, legenda ou tooltip, só a
 * silhueta da tendência ao lado do resultado principal do Dashboard. O
 * gráfico completo (com eixos/hover/tabela) mora na tela Gráficos —
 * ver EvolucaoChart. */
export function Sparkline({ valores, largura = 96, altura = 28 }: { valores: number[]; largura?: number; altura?: number }) {
  if (valores.length < 2) return null

  const min = Math.min(0, ...valores)
  const max = Math.max(0, ...valores)
  const escala = max - min || 1
  const passo = largura / (valores.length - 1)
  const pontos = valores
    .map((v, i) => `${(i * passo).toFixed(1)},${(altura - ((v - min) / escala) * altura).toFixed(1)}`)
    .join(' ')

  return (
    <svg width={largura} height={altura} viewBox={`0 0 ${largura} ${altura}`} className="sparkline" aria-hidden="true">
      <polyline
        points={pontos}
        fill="none"
        stroke="var(--sparkline-cor)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
