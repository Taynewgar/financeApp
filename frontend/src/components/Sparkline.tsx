import './sparkline.css'

/** Forma pura dos últimos meses — sem eixo, legenda ou tooltip, só a
 * silhueta da tendência ao lado de um KPI. Segue o contrato de "stat tile"
 * da skill de dataviz: linha no tom neutro (de-emphasis), ponto atual em
 * destaque na cor de acento — não repete a cor da série do valor (evita
 * "mais uma cor" competindo pela atenção num card pequeno). O gráfico
 * completo (com eixos/hover/tabela) mora na tela Gráficos — ver
 * EvolucaoChart/TaxaPoupancaChart. */
export function Sparkline({ valores, largura = 72, altura = 24 }: { valores: number[]; largura?: number; altura?: number }) {
  if (valores.length < 2) return null

  const min = Math.min(0, ...valores)
  const max = Math.max(0, ...valores)
  const escala = max - min || 1
  const passo = largura / (valores.length - 1)
  const coordX = (i: number) => i * passo
  const coordY = (v: number) => altura - ((v - min) / escala) * altura

  const pontos = valores.map((v, i) => `${coordX(i).toFixed(1)},${coordY(v).toFixed(1)}`).join(' ')
  const ultimoIndice = valores.length - 1

  return (
    <svg width={largura} height={altura} viewBox={`0 0 ${largura} ${altura}`} className="sparkline" aria-hidden="true">
      <polyline
        points={pontos}
        fill="none"
        stroke="var(--cor-texto-suave)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={coordX(ultimoIndice)} cy={coordY(valores[ultimoIndice])} r={3} fill="var(--cor-acento)" />
    </svg>
  )
}
