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

/** "Hoje" em YYYY-MM-DD no fuso LOCAL do aparelho — nunca UTC.
 * `new Date().toISOString()` sempre converte pra UTC, que desloca o dia
 * errado das ~21h às 23h59 num fuso negativo como o do Brasil (item 50
 * do backlog, achado em 2026-10-12: Dashboard/Gráficos abriam já no mês
 * seguinte, Novo Lançamento pré-preenchia a data de amanhã, nesse
 * horário). Usar os getters locais do `Date` (não `toISOString`) já
 * resolve isso E é dinâmico de propósito — segue o fuso que o aparelho
 * estiver configurado a qualquer momento (ex: usuário muda de cidade),
 * sem fixar "America/Sao_Paulo" (ou qualquer fuso) no código. */
export function hojeLocal(): string {
  const d = new Date()
  const ano = d.getFullYear()
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}
