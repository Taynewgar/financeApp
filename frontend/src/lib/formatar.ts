export function formatarMoeda(valor: number): string {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

/** dataISO no formato YYYY-MM-DD (como vem do backend) — evita passar por
 * Date/fuso, que desloca o dia em alguns horários. */
export function formatarData(dataISO: string): string {
  const [ano, mes, dia] = dataISO.split('-')
  return `${dia}/${mes}/${ano}`
}
