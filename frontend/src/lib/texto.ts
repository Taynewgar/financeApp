// Comparação de texto usada pra sugerir descrições já usadas no Novo
// Lançamento (item 43 do backlog) — chip de atalho + aviso de
// quase-duplicata. Mockado e calibrado antes de implementar (ver
// docs/backlog.md).

export function normalizarDescricao(texto: string): string {
  return texto.trim().toLowerCase().replace(/\s+/g, ' ')
}

// distância de edição (Levenshtein) entre 2 strings já normalizadas
export function distanciaLevenshtein(a: string, b: string): number {
  const m = a.length
  const n = b.length
  if (m === 0) return n
  if (n === 0) return m

  const dp = new Array<number>(n + 1)
  for (let j = 0; j <= n; j++) dp[j] = j

  for (let i = 1; i <= m; i++) {
    let anterior = dp[0]
    dp[0] = i
    for (let j = 1; j <= n; j++) {
      const atual = dp[j]
      dp[j] = a[i - 1] === b[j - 1] ? anterior : 1 + Math.min(anterior, dp[j], dp[j - 1])
      anterior = atual
    }
  }
  return dp[n]
}

// tolerância proporcional ao tamanho do texto: ~40%, no mínimo 1 e no
// máximo 5 caracteres — teto mantido pra descrição longa não ficar solta
// demais; percentual calibrado com o usuário via mockup interativo
export function limiteQuaseDuplicata(normalizado: string): number {
  return Math.max(1, Math.min(5, Math.round(normalizado.length * 0.4)))
}

// entre as `candidatas` (texto literal, como foi salvo), acha a primeira
// que é "quase igual" ao `atual` digitado (normalizado) mas não idêntica
// literalmente — null se nenhuma bater ou o texto for curto demais pra
// comparar com confiança (menos de 3 caracteres normalizados)
export function encontrarQuaseDuplicata(atual: string, candidatas: string[]): string | null {
  const norm = normalizarDescricao(atual)
  if (!atual || norm.length < 3) return null

  const limite = limiteQuaseDuplicata(norm)
  let melhor: string | null = null
  let melhorDistancia = Infinity

  for (const candidata of candidatas) {
    if (candidata === atual) continue
    const distancia = distanciaLevenshtein(norm, normalizarDescricao(candidata))
    if (distancia <= limite && distancia < melhorDistancia) {
      melhorDistancia = distancia
      melhor = candidata
    }
  }
  return melhor
}
