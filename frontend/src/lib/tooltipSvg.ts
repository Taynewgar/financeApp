/** Tooltip rico compartilhado pelos gráficos SVG de Gráficos (Comparador
 * de Séries, Ano a Ano, Caixinha Fluxo) — Rodada 104: geometria corrigida
 * de vez (usuário reportou caixa cortando a última linha e fonte
 * ilegível). A causa raiz: a altura/largura da caixa não reservava
 * espaço suficiente pro texto real (nem contava o tamanho do VALOR, só
 * do nome) — aqui o cálculo usa a linha inteira "nome: valor" e uma
 * altura de linha generosa o bastante pra nunca cortar a última linha. */

export type LinhaTooltip = { nome: string; cor: string; valor: string }

export type TooltipGeom = {
  rectX: number
  rectY: number
  largura: number
  altura: number
  textX: number
  titulo: string
  tituloY: number
  linhas: (LinhaTooltip & { y: number; swatchY: number })[]
}

const PADDING = 10
const ALTURA_LINHA = 19

/** `xPonto`/`yTopo` são coordenadas SVG (mesmo sistema do viewBox do
 * gráfico); `largImagem`/`margemDireita` definem onde a caixa não pode
 * passar pra não ser cortada pelo overflow:hidden padrão do <svg>. */
export function montarTooltip(
  titulo: string,
  linhasBase: LinhaTooltip[],
  xPonto: number,
  yTopo: number,
  largImagem: number,
  margemDireita: number,
): TooltipGeom | null {
  if (linhasBase.length === 0) return null

  const maiorConteudo = Math.max(titulo.length, ...linhasBase.map((l) => l.nome.length + 2 + l.valor.length))
  const largura = Math.min(320, Math.max(190, 60 + maiorConteudo * 6.6))
  const altura = PADDING * 2 + ALTURA_LINHA * (1 + linhasBase.length)

  const estouraDireita = xPonto + 14 + largura > largImagem - margemDireita - 6
  const rectX = estouraDireita ? xPonto - 14 - largura : xPonto + 14
  const rectY = yTopo
  const textX = rectX + 12

  const linhaTopo = (i: number) => rectY + PADDING + ALTURA_LINHA * i

  return {
    rectX,
    rectY,
    largura,
    altura,
    textX,
    titulo,
    tituloY: linhaTopo(0) + 14,
    linhas: linhasBase.map((l, i) => ({
      ...l,
      y: linhaTopo(i + 1) + 13,
      swatchY: linhaTopo(i + 1) + 5,
    })),
  }
}
