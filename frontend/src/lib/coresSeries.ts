// item 51 do backlog: paleta categórica compartilhada pelos gráficos
// comparativos (Comparador dinâmico, Ano a ano, Caixinhas) — cor por
// índice, não por tipo de dado, pra dar o máximo de séries distinguíveis
// visualmente antes de repetir.
export const PALETA_SERIES = [
  '#3987e5',
  '#d95926',
  '#199e70',
  '#a78bfa',
  '#f472b6',
  '#f59e0b',
  '#2dd4bf',
  '#60a5fa',
  '#fb7185',
  '#34d399',
  '#8b5cf6',
  '#eab308',
  '#5eead4',
  '#ec4899',
]

export function corDaSerie(indice: number): string {
  return PALETA_SERIES[indice % PALETA_SERIES.length]
}
