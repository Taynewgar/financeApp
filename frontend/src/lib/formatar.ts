export function formatarMoeda(valor: number, oculto = false): string {
  if (oculto) return '••••••'
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

/** Versão sem "R$"/centavos, abreviada acima de mil (ex: "1,8 mil") — pra
 * espaços apertados (cabeçalho fixo em telas pequenas) onde o valor
 * completo de formatarMoeda() não cabe sem quebrar/sobrepor texto (bug
 * reportado 2026-09-24 no resumo de alocação do Planejamento). */
export function formatarMoedaCompacta(valor: number, oculto = false): string {
  if (oculto) return '••••'
  return valor.toLocaleString('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })
}

/** dataISO no formato YYYY-MM-DD (como vem do backend) — evita passar por
 * Date/fuso, que desloca o dia em alguns horários. */
export function formatarData(dataISO: string): string {
  const [ano, mes, dia] = dataISO.split('-')
  return `${dia}/${mes}/${ano}`
}
