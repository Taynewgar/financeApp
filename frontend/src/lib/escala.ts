/** Degrau "redondo" (1/2/5 × potência de 10) pra um intervalo, mirando um
 * número alvo de marcações — mesma lógica de qualquer eixo de gráfico. */
function degrauAmigavel(intervalo: number, metaMarcacoes: number): number {
  if (intervalo <= 0) return 1
  const bruto = intervalo / metaMarcacoes
  const magnitude = 10 ** Math.floor(Math.log10(bruto))
  const resto = bruto / magnitude
  const residuoAmigavel = resto > 5 ? 10 : resto > 2 ? 5 : resto > 1 ? 2 : 1
  return residuoAmigavel * magnitude
}

/** Escala Y com marcações redondas — min/max sempre incluem 0 (valores
 * financeiros, positivos por padrão, mas podem ficar negativos). */
export function escalaY(valores: number[], metaMarcacoes = 4): { min: number; max: number; marcacoes: number[] } {
  const maximoBruto = Math.max(0, ...valores)
  const minimoBruto = Math.min(0, ...valores)
  const degrau = degrauAmigavel(maximoBruto - minimoBruto || 1, metaMarcacoes)
  const max = Math.ceil(maximoBruto / degrau) * degrau
  const min = Math.floor(minimoBruto / degrau) * degrau
  const marcacoes: number[] = []
  for (let v = min; v <= max + degrau / 2; v += degrau) {
    marcacoes.push(Math.round(v * 100) / 100)
  }
  return { min, max, marcacoes }
}
