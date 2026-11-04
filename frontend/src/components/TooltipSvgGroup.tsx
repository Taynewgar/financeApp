import type { TooltipGeom } from '../lib/tooltipSvg'

/** Renderização do tooltip rico compartilhado — ver lib/tooltipSvg.ts
 * pra geometria. Único lugar que desenha a caixa, pra garantir que os 4
 * gráficos de Gráficos fiquem visualmente idênticos (Rodada 104). */
export function TooltipSvgGroup({ tooltip }: { tooltip: TooltipGeom | null }) {
  if (!tooltip) return null
  return (
    <g>
      <rect
        x={tooltip.rectX}
        y={tooltip.rectY}
        width={tooltip.largura}
        height={tooltip.altura}
        rx={8}
        fill="var(--cor-superficie)"
        stroke="var(--cor-borda)"
        strokeWidth={1.5}
      />
      <text x={tooltip.textX} y={tooltip.tituloY} className="tooltip-svg-titulo">
        {tooltip.titulo}
      </text>
      {tooltip.linhas.map((l, i) => (
        <g key={i}>
          <rect x={tooltip.textX} y={l.swatchY} width={10} height={10} rx={2} fill={l.cor} />
          <text x={tooltip.textX + 15} y={l.y} className="tooltip-svg-texto">
            {l.nome}: {l.valor}
          </text>
        </g>
      ))}
    </g>
  )
}
